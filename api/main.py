from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
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


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def save_task_status(task_id: str, status: dict):
    """Сохранить статус задачи"""
    import asyncio
    asyncio.create_task(storage.set_task(task_id, status))
    logger.debug(f"Task {task_id} status updated: {status.get('status')}")

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
        
        # Определить region_id
        region_id = request.region_id
        
        # Если передан region_name вместо region_id, найти ID
        if not region_id and request.region_name:
            from utils import region_manager
            region = region_manager.get_by_name(request.region_name)
            if region:
                region_id = region['id']
                logger.info(f"📍 Resolved region '{request.region_name}' -> ID {region_id}")
        
        # Обновить статус
        save_task_status(task_id, {
            "status": "processing",
            "progress": 0,
            "message": "Получение SERP...",
            "created_at": datetime.utcnow().isoformat()
        })
        
        # === ШАГ 1: Получить SERP ===
        logger.info(f"🔍 Step 1: Fetching SERP for '{request.keyword}'")
        
        depth = request.settings.get("depth", 10)
        engine = request.settings.get("engine", "yandex")
        
        urls = await serp_service.get_results(
            keyword=request.keyword,
            region_id=region_id,
            depth=depth,
            engine=engine
        )
        
        if not urls:
            raise Exception("No URLs found in SERP")
        
        logger.info(f"✅ Found {len(urls)} URLs")
        
        save_task_status(task_id, {
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
        
        save_task_status(task_id, {
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
        
        save_task_status(task_id, {
            "status": "processing",
            "progress": 70,
            "message": f"Проанализировано {len(analysis_results)} сайтов. Агрегация...",
        })
        
        # === ШАГ 4: Агрегация ===
        logger.info(f"📊 Step 4: Aggregating entities")
        
        aggregated = aggregator_service.aggregate_entities(analysis_results)
        stats = aggregator_service.get_statistics(aggregated)
        
        logger.info(f"✅ Aggregated {len(aggregated)} unique entities")
        
        save_task_status(task_id, {
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
        save_task_status(task_id, {
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
        save_task_status(task_id, {
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
    
    # Сохранить начальный статус
    save_task_status(request.task_id, {
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