from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys
from datetime import datetime
import asyncio
from pathlib import Path
from services.storage_service import storage
from typing import Optional, Dict, List, Any
from config import settings
from config.constants import API_PREFIX
from models import (
    HealthResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    TaskStatusResponse,
    TaskListResponse,
    TaskDetailResponse,
)
from services import (
    serp_service,
    parser_service,
    llm_service,
    aggregator_service,
)
from utils import excel_generator


# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)


# === In-memory хранилище задач (для MVP) ===
# В production это будет Redis/PostgreSQL
# tasks_storage = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    logger.info("🚀 Starting SEO Entity Analyzer API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"OpenRouter Model: {settings.openrouter_model}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Storage Backend: {settings.storage_backend}")

    # Initialize database if using PostgreSQL
    if settings.storage_backend == "postgres" and settings.database_url:
        try:
            from db import init_db
            await init_db()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")

    yield

    logger.info("👋 Shutting down SEO Entity Analyzer API")


# Создание приложения
app = FastAPI(
    title="SEO Entity Analyzer",
    description="Автоматизированный сбор семантических сущностей для GEO/AEO продвижения",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Key middleware (опционально)
class APIKeyMiddleware(BaseHTTPMiddleware):
    """Проверка API ключа"""

    async def dispatch(self, request: Request, call_next):
        # Пропускаем публичные endpoints
        public_paths = ["/", "/health", f"{API_PREFIX}/health", f"{API_PREFIX}/docs", f"{API_PREFIX}/redoc", f"{API_PREFIX}/openapi.json"]

        if request.url.path in public_paths:
            return await call_next(request)

        # Если API_KEY установлен в настройках - требуем его
        if settings.api_key:
            api_key = request.headers.get("X-API-Key")

            if not api_key or api_key != settings.api_key:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid or missing API key"}
                )

        return await call_next(request)


# Добавляем middleware только если API_KEY установлен
if settings.api_key:
    app.add_middleware(APIKeyMiddleware)
    logger.info("🔒 API Key protection enabled")


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def save_task_status(task_id: str, status: dict):
    """Сохранить статус задачи"""
    try:
        await storage.set_task(task_id, status)
        logger.debug(f"Task {task_id} status updated: {status.get('status')}")
    except Exception as e:
        logger.error(f"Failed to save task status for {task_id}: {e}")

async def get_task_status(task_id: str) -> Optional[Dict]:
    """Получить статус задачи"""
    return await storage.get_task(task_id)

async def task_exists(task_id: str) -> bool:
    """Проверить существование задачи"""
    return await storage.exists(task_id)

async def run_analysis(request: AnalyzeRequest):
    """
    Главная функция анализа (выполняется в фоне)
    """
    
    task_id = request.task_id
    
    try:
        logger.info(f"🎬 Starting analysis for task {task_id}")

        # Определить region_id и region_name
        region_id = request.region_id
        region_name_resolved = request.region_name

        from utils import region_manager

        # Если передан region_name вместо region_id, найти ID
        if not region_id and region_name_resolved:
            region = region_manager.get_by_name(region_name_resolved)
            if region:
                region_id = region['id']
                region_name_resolved = region['title']
                logger.info(f"📍 Resolved region name '{request.region_name}' -> ID {region_id}")

        # Если передан region_id, но нет region_name, разрешить имя
        if region_id and (not region_name_resolved or not region_name_resolved.strip()):
            region = region_manager.get_by_id(region_id)
            if region:
                region_name_resolved = region['title']
                logger.info(f"📍 Resolved region ID {region_id} -> '{region_name_resolved}'")

        # Параметры анализа
        depth = request.settings.get("depth", 10)
        engine = request.settings.get("engine", "yandex")

        # Обновить статус (сохраняем все параметры задачи)
        await save_task_status(task_id, {
            "task_name": request.task_name,
            "keyword": request.keyword,
            "region_id": region_id,
            "region_name": region_name_resolved,
            "engine": engine,
            "depth": depth,
            "status": "processing",
            "progress": 0,
            "message": "Получение SERP...",
        })

        # === ШАГ 1: Получить SERP ===
        logger.info(f"🔍 Step 1: Fetching SERP for '{request.keyword}'")

        # Запрашиваем больше URLs для компенсации неудачных парсингов
        multiplier = settings.serp_fetch_multiplier
        initial_fetch_depth = min(depth * multiplier, 100)  # max 100 (API limit)

        logger.info(f"📊 Target: {depth} results, Fetching: {initial_fetch_depth} URLs (multiplier={multiplier})")

        urls = await serp_service.get_results(
            keyword=request.keyword,
            region_id=region_id,
            depth=initial_fetch_depth,
            engine=engine
        )

        if not urls:
            raise Exception("No URLs found in SERP")

        logger.info(f"✅ Found {len(urls)} URLs from SERP")

        await save_task_status(task_id, {
            "status": "processing",
            "progress": 20,
            "message": f"Найдено {len(urls)} URL. Извлечение контента...",
        })

        # === ШАГ 2: Извлечь контент ===
        logger.info(f"📥 Step 2: Extracting content from {len(urls)} URLs")

        contents = await parser_service.extract_multiple(urls)

        if not contents:
            raise Exception("Failed to extract content from any URL")

        logger.info(f"✅ Extracted content from {len(contents)}/{len(urls)} URLs")

        # === ШАГ 2.5: Fallback - дозапросить URLs если не хватает ===
        processed_urls = set(urls)
        max_fallback_attempts = 3
        fallback_attempt = 0
        current_fetch_depth = initial_fetch_depth

        while len(contents) < depth and fallback_attempt < max_fallback_attempts and current_fetch_depth < 100:
            needed = depth - len(contents)
            fallback_attempt += 1

            # Увеличиваем depth для следующего запроса
            current_fetch_depth = min(current_fetch_depth + (needed * multiplier), 100)

            logger.info(f"🔄 Fallback attempt {fallback_attempt}/{max_fallback_attempts}: Need {needed} more, fetching up to {current_fetch_depth} URLs")

            additional_urls = await serp_service.get_results(
                keyword=request.keyword,
                region_id=region_id,
                depth=current_fetch_depth,
                engine=engine
            )

            # Фильтруем уже обработанные URL
            new_urls = [url for url in additional_urls if url not in processed_urls]

            if not new_urls:
                logger.warning(f"⚠️ No new URLs available from SERP (all duplicates)")
                break

            logger.info(f"📥 Found {len(new_urls)} new URLs to process")

            # Парсим новые URL
            new_contents = await parser_service.extract_multiple(new_urls)

            if new_contents:
                contents.extend(new_contents)
                logger.info(f"✅ Extracted {len(new_contents)} more contents. Total: {len(contents)}/{depth}")

            # Добавляем в processed
            processed_urls.update(new_urls)

            # Если достигли цели, выходим
            if len(contents) >= depth:
                logger.info(f"🎯 Target reached: {len(contents)}/{depth} results")
                break

        # Ограничиваем до требуемого количества (берем первые N успешных)
        if len(contents) > depth:
            logger.info(f"📊 Limiting results from {len(contents)} to {depth} (as requested)")
            contents = contents[:depth]
        elif len(contents) < depth:
            logger.warning(f"⚠️ Could only extract {len(contents)}/{depth} requested results after {fallback_attempt} fallback attempts")
            logger.warning(f"💡 Consider increasing SERP_FETCH_MULTIPLIER (current: {multiplier}), checking blacklist, or improving parsing algorithms")

        logger.info(f"✅ Final: Using {len(contents)} successfully parsed URLs")
        
        await save_task_status(task_id, {
            "status": "processing",
            "progress": 40,
            "message": f"Извлечен контент с {len(contents)} сайтов. Анализ с помощью ИИ...",
        })
        
        # === ШАГ 3: ИИ анализ (параллельно) ===
        logger.info(f"🤖 Step 3: AI analysis of {len(contents)} pages")
        
        tasks = [
            llm_service.analyze_url(c['url'], c['text'])
            for c in contents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные
        analysis_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Analysis failed for URL {i}: {result}")
                continue
            analysis_results.append(result)
        
        if not analysis_results:
            raise Exception("AI analysis failed for all pages")
        
        logger.info(f"✅ Successfully analyzed {len(analysis_results)} pages")
        
        await save_task_status(task_id, {
            "status": "processing",
            "progress": 70,
            "message": f"Проанализировано {len(analysis_results)} сайтов. Агрегация...",
        })
        
        # === ШАГ 4: Агрегация ===
        logger.info(f"📊 Step 4: Aggregating entities")
        
        aggregated = aggregator_service.aggregate_entities(analysis_results)
        stats = aggregator_service.get_statistics(aggregated)
        
        logger.info(f"✅ Aggregated {len(aggregated)} unique entities")
        
        await save_task_status(task_id, {
            "status": "processing",
            "progress": 90,
            "message": "Генерация Excel отчета...",
        })
        
        # === ШАГ 5: Генерация Excel ===
        logger.info(f"📊 Step 5: Generating Excel report")
        
        metadata = {
            "keyword": request.keyword,
            "region_id": region_id,
            "region_name": request.region_name,
            "engine": engine,
            "total_sources": len(analysis_results),
            "task_id": task_id,
        }
        
        excel_filename = f"{task_id}.xlsx"
        excel_path = excel_generator.generate_report(
            aggregated_entities=aggregated,
            metadata=metadata,
            filename=excel_filename
        )
        
        logger.info(f"✅ Report generated: {excel_path}")
        
        # === ФИНАЛ: Сохранить результат ===
        await save_task_status(task_id, {
            "status": "completed",
            "progress": 100,
            "message": "Анализ завершен",
            "results": {
                "total_entities": len(aggregated),
                "total_sources": len(analysis_results),
                "universal_entities": stats["universal_entities"],
                "common_entities": stats["common_entities"],
                "rare_entities": stats["rare_entities"],
                "excel_file": excel_filename,
            }
        })
        
        logger.info(f"🎉 Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {str(e)}", exc_info=True)
        await save_task_status(task_id, {
            "status": "failed",
            "progress": 0,
            "message": f"Ошибка: {str(e)}",
            "error": str(e)
        })


# === ENDPOINTS ===

@app.get("/", tags=["Root"])
async def root():
    """Корневой endpoint"""
    return {
        "service": "SEO Entity Analyzer",
        "version": "1.0.0",
        "status": "running",
        "docs": f"{API_PREFIX}/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@app.get(f"{API_PREFIX}/health", response_model=HealthResponse, tags=["Health"])
async def api_health_check():
    """API Health check endpoint"""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@app.post(f"{API_PREFIX}/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Запуск анализа SERP и извлечение сущностей
    """
    
    logger.info(f"📥 New analysis request: task_id={request.task_id}, keyword='{request.keyword}'")

    # Проверка что задача не существует
    if await task_exists(request.task_id):
        raise HTTPException(
            status_code=400,
            detail=f"Task with ID '{request.task_id}' already exists"
        )

    # Разрешить region_name если передан только region_id
    region_name = request.region_name
    region_id = request.region_id

    logger.debug(f"📍 Initial values: region_id={region_id}, region_name={repr(region_name)}")

    # Если region_name пустой (None или пустая строка), но есть region_id - разрешить
    if (not region_name or not region_name.strip()) and region_id:
        from utils import region_manager
        region = region_manager.get_by_id(region_id)
        if region:
            region_name = region['title']
            logger.info(f"📍 Resolved region_id {region_id} -> '{region_name}'")
        else:
            logger.warning(f"⚠️ Could not resolve region_id {region_id}")

    # Сохранить начальный статус
    await save_task_status(request.task_id, {
        "task_name": request.task_name,
        "keyword": request.keyword,
        "region_id": region_id,
        "region_name": region_name,
        "engine": request.settings.get("engine", "yandex"),
        "depth": request.settings.get("depth", 10),
        "created_by": request.created_by,
        "status": "queued",
        "progress": 0,
        "message": "Задача в очереди",
        "created_at": datetime.utcnow().isoformat()
    })
    
    # Запускаем async задачу правильно
    asyncio.create_task(run_analysis(request))
    
    return AnalyzeResponse(
        task_id=request.task_id,
        status="queued",
        message=f"Задача '{request.task_id}' поставлена в очередь"
    )


@app.get(f"{API_PREFIX}/status/{{task_id}}", response_model=TaskStatusResponse, tags=["Status"])
async def get_status(task_id: str):
    """
    Получить статус выполнения задачи
    """
    
    logger.debug(f"📊 Status check for task: {task_id}")
    
    # Используем get_task_status
    task_data = await get_task_status(task_id)
    
    if not task_data:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{task_id}' not found"
        )
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task_data.get("status"),
        progress=task_data.get("progress"),
        results=task_data.get("results"),
        error=task_data.get("error"),
        created_at=task_data.get("created_at"),
        updated_at=task_data.get("updated_at")
    )


@app.get(f"{API_PREFIX}/download/{{task_id}}", tags=["Download"])
async def download_report(task_id: str):
    """
    Скачать Excel отчет
    """
    
    logger.info(f"📥 Download request for task: {task_id}")
    
    # Используем get_task_status
    task_data = await get_task_status(task_id)
    
    if not task_data:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{task_id}' not found"
        )
    
    if task_data.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed yet. Status: {task_data.get('status')}"
        )
    
    excel_filename = task_data.get("results", {}).get("excel_file")
    
    if not excel_filename:
        raise HTTPException(
            status_code=404,
            detail="Report file not found"
        )
    
    file_path = Path("reports") / excel_filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report file does not exist"
        )
    
    return FileResponse(
        path=file_path,
        filename=excel_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get(f"{API_PREFIX}/tasks", response_model=TaskListResponse, tags=["Tasks"])
async def list_tasks(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    created_by: Optional[str] = None
):
    """
    Получить список всех задач с пагинацией

    **Параметры:**
    - page: Номер страницы (по умолчанию 1)
    - per_page: Количество на странице (по умолчанию 20, макс 100)
    - status: Фильтр по статусу (queued/processing/completed/failed)

    **Возвращает:**
    - total: Общее количество задач
    - page: Текущая страница
    - per_page: Элементов на странице
    - items: Список задач (краткая информация)

    **Пример:**
    ```
    GET /api/v1/tasks?page=1&per_page=20&status=completed

    {
      "total": 42,
      "page": 1,
      "per_page": 20,
      "items": [...]
    }
    ```
    """

    # Validate params
    if per_page > 100:
        raise HTTPException(status_code=400, detail="per_page cannot exceed 100")
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")

    try:
        result = await storage.list_tasks(page=page, per_page=per_page, status=status, created_by=created_by)

        # Format items for response
        items = []
        for task in result["items"]:
            item = {
                "task_id": task["task_id"],
                "task_name": task.get("task_name"),
                "keyword": task.get("keyword", ""),
                "region_name": task.get("region_name"),
                "engine": task.get("engine"),
                "status": task["status"],
                "progress": task.get("progress"),
                "created_at": task.get("created_at"),
            }

            # Extract stats from results
            if task.get("results"):
                item["total_entities"] = task["results"].get("total_entities")
                item["total_sources"] = task["results"].get("total_sources")
            else:
                item["total_entities"] = None
                item["total_sources"] = None

            items.append(item)

        return {
            "total": result["total"],
            "page": result["page"],
            "per_page": result["per_page"],
            "items": items
        }

    except Exception as e:
        logger.error(f"❌ Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@app.get(f"{API_PREFIX}/tasks/{{task_id}}", response_model=TaskDetailResponse, tags=["Tasks"])
async def get_task_detail(task_id: str):
    """
    Получить детальную информацию о задаче

    **Параметры:**
    - task_id: ID задачи

    **Возвращает:**
    - Полная информация о задаче с результатами

    **Пример:**
    ```
    GET /api/v1/tasks/task-1769078061071

    {
      "task_id": "task-1769078061071",
      "task_name": "Анализ займов Москва",
      "keyword": "займ денег до зарплаты",
      "status": "completed",
      "results": {...},
      ...
    }
    ```
    """

    task = await get_task_status(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


@app.delete(f"{API_PREFIX}/tasks/{{task_id}}", tags=["Tasks"])
async def delete_task(task_id: str):
    """
    Удалить задачу по ID

    **Параметры:**
    - task_id: ID задачи для удаления

    **Возвращает:**
    - Статус удаления

    **Пример:**
    ```
    DELETE /api/v1/tasks/task-1769078061071

    {
      "success": true,
      "message": "Task deleted successfully"
    }
    ```
    """

    # Проверить существование задачи
    task = await get_task_status(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Удалить задачу
    success = await storage.delete_task(task_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete task"
        )

    logger.info(f"🗑️ Task {task_id} deleted successfully")

    return {
        "success": True,
        "message": "Task deleted successfully"
    }


@app.get(f"{API_PREFIX}/regions/search", tags=["Regions"])
async def search_regions(q: str, limit: int = 10):
    """
    Поиск регионов для автокомплита
    
    **Параметры:**
    - q: Поисковый запрос (минимум 2 символа)
    - limit: Максимум результатов (по умолчанию 10)
    
    **Возвращает:**
    - Список регионов [{"id": int, "title": str, "parent": int}, ...]
    
    **Пример:**
```
    GET /api/v1/regions/search?q=Моск
    
    [
      {"id": 213, "title": "Москва", "parent": 1},
      {"id": 1, "title": "Москва и область", "parent": 3}
    ]
```
    """
    
    from utils import region_manager
    
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Query must be at least 2 characters"
        )
    
    results = region_manager.search(q, limit=limit)
    
    return results


@app.get(f"{API_PREFIX}/regions/{{region_id}}", tags=["Regions"])
async def get_region(region_id: int):
    """
    Получить регион по ID
    
    **Параметры:**
    - region_id: ID региона
    
    **Возвращает:**
    - Регион {"id": int, "title": str, "parent": int}
    """
    
    from utils import region_manager
    
    region = region_manager.get_by_id(region_id)
    
    if not region:
        raise HTTPException(
            status_code=404,
            detail=f"Region with ID {region_id} not found"
        )
    
    return region


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик ошибок"""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )