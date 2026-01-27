from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from loguru import logger

from openpyxl import Workbook
from openpyxl.styles import (
    Font, 
    Alignment, 
    PatternFill, 
    Border, 
    Side
)
from openpyxl.utils import get_column_letter


class ExcelGenerator:
    """Генератор Excel отчетов"""
    
    def __init__(self):
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_report(
        self,
        aggregated_entities: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        filename: str = None
    ) -> str:
        """
        Сгенерировать Excel отчет
        
        Args:
            aggregated_entities: Агрегированные сущности
            metadata: Метаданные (keyword, region, total_sources, etc.)
            filename: Имя файла (опционально)
            
        Returns:
            Путь к сгенерированному файлу
        """
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"seo_entities_{timestamp}.xlsx"
        
        filepath = self.reports_dir / filename
        
        logger.info(f"📊 Generating Excel report: {filename}")
        
        # Создать workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Entities Report"
        
        # === ЗАГОЛОВОК ===
        self._add_header(ws, metadata)
        
        # === ТАБЛИЦА СУЩНОСТЕЙ ===
        self._add_entities_table(ws, aggregated_entities, metadata)
        
        # === СТАТИСТИКА ===
        self._add_statistics(ws, aggregated_entities, metadata)
        
        # Сохранить
        wb.save(filepath)
        
        logger.info(f"✅ Report saved: {filepath}")
        
        return str(filepath)
    
    def _add_header(self, ws, metadata: Dict):
        """Добавить заголовок отчета"""
        
        # Заголовок
        ws['A1'] = "Отчет по анализу сущностей для SEO"
        ws['A1'].font = Font(size=16, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells('A1:E1')
        ws.row_dimensions[1].height = 30
        
        # Метаданные
        row = 3
        ws[f'A{row}'] = "Запрос:"
        ws[f'B{row}'] = metadata.get('keyword', 'Не указан')
        ws[f'A{row}'].font = Font(bold=True)
        
        row += 1
        
        # Регион (с учетом region_id и region_name)
        region_text = metadata.get('region_name', '')
        region_id = metadata.get('region_id')
        if region_id and not region_text:
            # Попробовать получить название по ID
            from utils import region_manager
            region = region_manager.get_by_id(region_id)
            if region:
                region_text = region['title']
        
        ws[f'A{row}'] = "Регион:"
        ws[f'B{row}'] = region_text or 'Не указан'
        ws[f'A{row}'].font = Font(bold=True)
        
        row += 1
        
        # Поисковая система
        engine = metadata.get('engine', 'yandex')
        engine_display = "Яндекс" if engine == "yandex" else "Google"
        
        ws[f'A{row}'] = "Поисковая система:"
        ws[f'B{row}'] = engine_display
        ws[f'A{row}'].font = Font(bold=True)
        
        row += 1

        ws[f'A{row}'] = "Проанализировано страниц:"
        ws[f'B{row}'] = metadata.get('total_sources', 0)
        ws[f'A{row}'].font = Font(bold=True)

        row += 1

        ws[f'A{row}'] = "Уникальных доменов:"
        ws[f'B{row}'] = metadata.get('total_domains', metadata.get('total_sources', 0))
        ws[f'A{row}'].font = Font(bold=True)

        row += 1
        ws[f'A{row}'] = "Дата создания:"
        ws[f'B{row}'] = datetime.now().strftime("%d.%m.%Y %H:%M")
        ws[f'A{row}'].font = Font(bold=True)
    
    def _add_entities_table(self, ws, entities: List[Dict], metadata: Dict):
        """Добавить таблицу сущностей"""

        # Начало таблицы (сдвинуто на 1 строку из-за доп. метаданных)
        table_start_row = 11

        # Заголовки колонок (НА РУССКОМ!)
        headers = ["№", "Сущность 1", "Связь", "Сущность 2", "Частота", "Домены"]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=table_start_row, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="5B9BD5", end_color="5B9BD5", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = self._get_border()
        
        # Данные
        total_sources = metadata.get('total_sources', 1)
        
        for idx, entity in enumerate(entities, 1):
            row = table_start_row + idx
            
            # Номер
            cell = ws.cell(row=row, column=1, value=idx)
            cell.alignment = Alignment(horizontal="center")
            cell.border = self._get_border()
            
            # Entity 1
            cell = ws.cell(row=row, column=2, value=entity['entity_1'])
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            cell.border = self._get_border()
            
            # Relation
            cell = ws.cell(row=row, column=3, value=entity['relation'])
            cell.alignment = Alignment(horizontal="center")
            cell.border = self._get_border()
            
            # Entity 2
            cell = ws.cell(row=row, column=4, value=entity['entity_2'])
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            cell.border = self._get_border()
            
            # Frequency [X/Y]
            count = entity['count']
            freq_text = f"[{count}/{total_sources}]"
            cell = ws.cell(row=row, column=5, value=freq_text)
            cell.alignment = Alignment(horizontal="center")
            cell.border = self._get_border()
            
            # Цветовое выделение по частоте
            if count == total_sources:
                # Зеленый - у всех
                cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                cell.font = Font(bold=True, color="006100")
            elif count >= total_sources / 2:
                # Желтый - у большинства
                cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                cell.font = Font(color="9C6500")
            else:
                # Красный - редкие
                cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                cell.font = Font(color="9C0006")
            
            # Domains (первые 3)
            # schema_version=2 использует 'domains' для списка уникальных доменов
            domains = entity.get('domains') or []
            domains_text = "\n".join(domains[:3])
            if len(domains) > 3:
                domains_text += f"\n...ещё {len(domains) - 3}"

            cell = ws.cell(row=row, column=6, value=domains_text)
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            cell.border = self._get_border()
        
        # Ширина колонок
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 35
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 50
        
        # Высота строк данных
        for r in range(table_start_row + 1, table_start_row + len(entities) + 1):
            ws.row_dimensions[r].height = 40

    def _add_statistics(self, ws, entities: List[Dict], metadata: Dict):
        """Добавить статистику внизу"""

        # Таблица начинается с 11 строки
        stats_row = 11 + len(entities) + 3
        
        ws[f'A{stats_row}'] = "Сводная статистика"
        ws[f'A{stats_row}'].font = Font(size=12, bold=True)
        
        stats_row += 2
        
        total_sources = metadata.get('total_sources', 1)
        
        # Подсчет статистики
        universal = sum(1 for e in entities if e['count'] == total_sources)
        common = sum(1 for e in entities if e['count'] >= total_sources / 2)
        rare = sum(1 for e in entities if e['count'] <= 2)
        
        stats = [
            ("Всего уникальных сущностей", len(entities)),
            ("Универсальные (у всех сайтов)", universal),
            ("Частые (у >50% сайтов)", common),
            ("Редкие (у 1-2 сайтов)", rare),
        ]
        
        for label, value in stats:
            ws[f'A{stats_row}'] = label
            ws[f'B{stats_row}'] = value
            ws[f'A{stats_row}'].font = Font(bold=True)
            stats_row += 1
    
    def _get_border(self):
        """Получить стиль границ"""
        thin_border = Side(style='thin', color='000000')
        return Border(
            left=thin_border,
            right=thin_border,
            top=thin_border,
            bottom=thin_border
        )


# Глобальный экземпляр
excel_generator = ExcelGenerator()