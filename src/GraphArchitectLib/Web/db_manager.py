#!/usr/bin/env python
"""
Утилита управления SQLite базой данных.

Команды:
    python db_manager.py init           - Создать таблицы
    python db_manager.py load_agents    - Загрузить агентов из agent_library
    python db_manager.py list_agents    - Показать всех агентов
    python db_manager.py stats          - Статистика БД
    python db_manager.py clear          - Очистить все данные
    python db_manager.py backup         - Создать backup
"""

import sys
import argparse
from pathlib import Path
import shutil
from datetime import datetime

from database import get_database
from sqlite_repository import get_sqlite_repository


def init_database(args):
    """Инициализировать базу данных"""
    print("\n" + "="*70)
    print("📦 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("="*70)
    
    db = get_database(args.db_path)
    
    print(f"\n✅ База данных инициализирована: {args.db_path}")
    print("\nТаблицы:")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table['name']}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table['name']:20} ({count} записей)")
    
    print("\n" + "="*70)


def load_agents(args):
    """Загрузить агентов из agent_library.py в БД"""
    print("\n" + "="*70)
    print("📥 ЗАГРУЗКА АГЕНТОВ В БАЗУ ДАННЫХ")
    print("="*70)
    
    db = get_database(args.db_path)
    
    # Очищаем существующих агентов если флаг установлен
    if args.force:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM agents")
            print("  ⚠️ Существующие агенты удалены")
    
    # Загружаем агентов
    db.insert_default_agents()
    
    # Показываем результат
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agents")
        count = cursor.fetchone()[0]
        
        print(f"\n✅ В БД сейчас {count} агентов")
    
    print("="*70)


def list_agents(args):
    """Показать список всех агентов"""
    print("\n" + "="*70)
    print("👥 СПИСОК АГЕНТОВ В БД")
    print("="*70)
    
    repo = get_sqlite_repository(args.db_path)
    agents = repo.get_all_agents()
    
    if not agents:
        print("\n  ⚠️ Агенты не найдены")
        print("  Выполните: python db_manager.py load_agents")
        return
    
    print(f"\nВсего агентов: {len(agents)}\n")
    
    # Группируем по типу
    by_type = {}
    for agent in agents:
        if agent.type not in by_type:
            by_type[agent.type] = []
        by_type[agent.type].append(agent)
    
    for agent_type, agents_list in sorted(by_type.items()):
        print(f"\n{agent_type.upper()} ({len(agents_list)}):")
        print("-" * 70)
        
        for agent in sorted(agents_list, key=lambda a: a.name):
            metrics_str = ""
            if agent.metrics:
                score = agent.metrics.get('avgScore', 0)
                time_ms = agent.metrics.get('avgResponseTime', 0)
                metrics_str = f"score={score:.2f}, time={time_ms}ms"
            
            print(f"  {agent.icon} {agent.name:30} ${agent.cost:.3f} {metrics_str}")
    
    print("\n" + "="*70)


def show_statistics(args):
    """Показать статистику БД"""
    print("\n" + "="*70)
    print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
    print("="*70)
    
    db = get_database(args.db_path)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Статистика по таблицам
        tables = [
            'agents', 'workflows', 'chats', 'documents', 
            'executions', 'feedbacks', 'tool_metrics'
        ]
        
        print("\nРазмер таблиц:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table:20} {count:>6} записей")
            except:
                print(f"  {table:20} [не существует]")
        
        # Статистика выполнений
        cursor.execute("SELECT COUNT(*) FROM executions WHERE status = 'COMPLETED'")
        completed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM executions WHERE status = 'FAILED'")
        failed = cursor.fetchone()[0]
        
        total_exec = completed + failed
        
        if total_exec > 0:
            print(f"\nВыполнения:")
            print(f"  Завершено:  {completed} ({completed/total_exec*100:.1f}%)")
            print(f"  Провалено:  {failed} ({failed/total_exec*100:.1f}%)")
        
        # Средняя оценка качества
        cursor.execute("SELECT AVG(quality_score) FROM feedbacks")
        avg_quality = cursor.fetchone()[0]
        
        if avg_quality:
            print(f"\nКачество:")
            print(f"  Средняя оценка: {avg_quality:.3f}")
        
        # Размер файла БД
        db_file = Path(args.db_path)
        if db_file.exists():
            size_mb = db_file.stat().st_size / (1024 * 1024)
            print(f"\nФайл БД:")
            print(f"  Путь: {db_file.absolute()}")
            print(f"  Размер: {size_mb:.2f} МБ")
    
    print("\n" + "="*70)


def clear_data(args):
    """Очистить все данные"""
    print("\n" + "="*70)
    print("⚠️ ОЧИСТКА ДАННЫХ")
    print("="*70)
    
    if not args.force:
        response = input("\nВы уверены? Все данные будут удалены! (yes/no): ")
        if response.lower() != 'yes':
            print("Отменено")
            return
    
    db = get_database(args.db_path)
    db.clear_all_data()
    
    print("\n✅ Все данные очищены")
    print("="*70)


def backup_database(args):
    """Создать backup БД"""
    print("\n" + "="*70)
    print("💾 BACKUP БАЗЫ ДАННЫХ")
    print("="*70)
    
    db_file = Path(args.db_path)
    
    if not db_file.exists():
        print(f"\n❌ Файл БД не найден: {args.db_path}")
        return
    
    # Создаем имя backup файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = db_file.parent / f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"
    
    # Копируем файл
    shutil.copy2(db_file, backup_file)
    
    size_mb = backup_file.stat().st_size / (1024 * 1024)
    
    print(f"\n✅ Backup создан:")
    print(f"  Файл: {backup_file}")
    print(f"  Размер: {size_mb:.2f} МБ")
    print("\n" + "="*70)


def add_agent(args):
    """Добавить нового агента вручную"""
    print("\n" + "="*70)
    print("➕ ДОБАВЛЕНИЕ АГЕНТА")
    print("="*70)
    
    from models import Agent
    from sqlite_repository import get_sqlite_repository
    
    # Интерактивный ввод
    agent_id = input("ID агента: ") or f"agent-{uuid.uuid4().hex[:8]}"
    name = input("Название: ") or "New Agent"
    agent_type = input("Тип (classification/writing/research и т.д.): ") or "general"
    icon = input("Иконка (emoji): ") or "🤖"
    color = input("Цвет (hex): ") or "#6366f1"
    specialization = input("Специализация: ") or ""
    cost = float(input("Стоимость ($): ") or "0.01")
    
    agent = Agent(
        id=agent_id,
        name=name,
        type=agent_type,
        icon=icon,
        color=color,
        specialization=specialization,
        capabilities=[],
        cost=cost,
        metrics={
            "avgScore": 0.5,
            "avgResponseTime": 3000
        }
    )
    
    repo = get_sqlite_repository(args.db_path)
    repo.save_agent(agent)
    
    print(f"\n✅ Агент добавлен: {agent.name} ({agent.id})")
    print("="*70)


def export_agents(args):
    """Экспортировать агентов в JSON"""
    print("\n" + "="*70)
    print("📤 ЭКСПОРТ АГЕНТОВ")
    print("="*70)
    
    repo = get_sqlite_repository(args.db_path)
    agents = repo.get_all_agents()
    
    output_file = args.output or "agents_export.json"
    
    # Конвертируем в JSON
    agents_data = [
        {
            'id': a.id,
            'name': a.name,
            'type': a.type,
            'icon': a.icon,
            'color': a.color,
            'specialization': a.specialization,
            'capabilities': a.capabilities,
            'cost': a.cost,
            'metrics': a.metrics
        }
        for a in agents
    ]
    
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(agents_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Экспортировано {len(agents)} агентов в {output_file}")
    print("="*70)


def import_agents(args):
    """Импортировать агентов из JSON"""
    print("\n" + "="*70)
    print("📥 ИМПОРТ АГЕНТОВ")
    print("="*70)
    
    import json
    from models import Agent
    from sqlite_repository import get_sqlite_repository
    
    input_file = args.input
    
    if not Path(input_file).exists():
        print(f"\n❌ Файл не найден: {input_file}")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        agents_data = json.load(f)
    
    repo = get_sqlite_repository(args.db_path)
    
    imported = 0
    for data in agents_data:
        agent = Agent(**data)
        repo.save_agent(agent)
        imported += 1
    
    print(f"\n✅ Импортировано агентов: {imported}")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Утилита управления SQLite БД для GraphArchitect",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--db-path',
        default='grapharchitect.db',
        help='Путь к файлу БД (по умолчанию: grapharchitect.db)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # init
    subparsers.add_parser('init', help='Инициализировать БД (создать таблицы)')
    
    # load_agents
    load_parser = subparsers.add_parser('load_agents', help='Загрузить агентов из agent_library')
    load_parser.add_argument('--force', action='store_true', help='Перезаписать существующих')
    
    # list_agents
    subparsers.add_parser('list_agents', help='Показать всех агентов')
    
    # stats
    subparsers.add_parser('stats', help='Показать статистику БД')
    
    # clear
    clear_parser = subparsers.add_parser('clear', help='Очистить все данные')
    clear_parser.add_argument('--force', action='store_true', help='Без подтверждения')
    
    # backup
    subparsers.add_parser('backup', help='Создать backup БД')
    
    # add_agent
    subparsers.add_parser('add_agent', help='Добавить нового агента (интерактивно)')
    
    # export
    export_parser = subparsers.add_parser('export', help='Экспортировать агентов в JSON')
    export_parser.add_argument('--output', help='Выходной файл', default='agents_export.json')
    
    # import
    import_parser = subparsers.add_parser('import_agents', help='Импортировать агентов из JSON')
    import_parser.add_argument('--input', required=True, help='Входной JSON файл')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Выполняем команду
    commands = {
        'init': init_database,
        'load_agents': load_agents,
        'list_agents': list_agents,
        'stats': show_statistics,
        'clear': clear_data,
        'backup': backup_database,
        'add_agent': add_agent,
        'export': export_agents,
        'import_agents': import_agents
    }
    
    command_func = commands.get(args.command)
    if command_func:
        try:
            command_func(args)
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"❌ Неизвестная команда: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
