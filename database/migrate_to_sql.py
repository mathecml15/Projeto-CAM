"""
================================================================================
SCRIPT DE MIGRAÇÃO - Migra usuários de JSON para SQL
================================================================================

Este script migra os usuários do arquivo users.json para o banco de dados SQL.

COMO USAR:
1. Execute: python migrate_to_sql.py
2. O script irá:
   - Criar o banco de dados (se não existir)
   - Criar as tabelas necessárias
   - Migrar todos os usuários do JSON para o SQL
   - Mostrar estatísticas da migração

APÓS A MIGRAÇÃO:
- Os usuários estarão no banco de dados SQL
- O arquivo users.json pode ser mantido como backup
- O sistema usará automaticamente o banco de dados
"""

import os
from database import init_database, migrate_from_json, get_database_stats

def main():
    """
    Função principal que executa a migração.
    """
    print("=" * 70)
    print("MIGRAÇÃO DE USUÁRIOS: JSON -> SQL")
    print("=" * 70)
    print()
    
    # Verifica se o arquivo users.json existe
    json_file = "users.json"
    if not os.path.exists(json_file):
        print(f"⚠️  Arquivo {json_file} não encontrado.")
        print("   Nenhum usuário para migrar.")
        print()
        print("   Vamos apenas inicializar o banco de dados...")
        print()
        
        # Inicializa o banco de dados mesmo sem arquivo JSON
        try:
            init_database()
            print("✅ Banco de dados inicializado com sucesso!")
            print()
            
            # Mostra estatísticas
            stats = get_database_stats()
            print("Estatísticas do banco de dados:")
            print(f"  - Tipo: {stats['db_type']}")
            print(f"  - Arquivo: {stats['db_file']}")
            print(f"  - Total de usuários: {stats['total_users']}")
            print()
            
        except Exception as e:
            print(f"❌ Erro ao inicializar banco de dados: {e}")
            return
        
        print("✅ Pronto! O sistema agora está usando banco de dados SQL.")
        print("   Você pode criar novos usuários através da interface web.")
        return
    
    # Inicializa o banco de dados
    print("1. Inicializando banco de dados...")
    try:
        init_database()
        print("   ✅ Banco de dados inicializado!")
    except Exception as e:
        print(f"   ❌ Erro ao inicializar banco de dados: {e}")
        return
    
    print()
    print("2. Migrando usuários do JSON para o SQL...")
    print()
    
    # Migra os usuários
    success_count, error_count, errors = migrate_from_json(json_file)
    
    print()
    print("=" * 70)
    print("RESUMO DA MIGRAÇÃO")
    print("=" * 70)
    print(f"✅ Usuários migrados com sucesso: {success_count}")
    print(f"❌ Erros: {error_count}")
    print()
    
    # Mostra estatísticas do banco de dados
    try:
        stats = get_database_stats()
        print("Estatísticas do banco de dados:")
        print(f"  - Tipo: {stats['db_type']}")
        print(f"  - Arquivo: {stats['db_file']}")
        print(f"  - Total de usuários: {stats['total_users']}")
        print(f"  - Usuários ativos: {stats['active_users']}")
        print(f"  - Usuários inativos: {stats['inactive_users']}")
        print()
    except Exception as e:
        print(f"⚠️  Erro ao obter estatísticas: {e}")
        print()
    
    if success_count > 0:
        print("✅ Migração concluída com sucesso!")
        print()
        print("📝 PRÓXIMOS PASSOS:")
        print("   1. O sistema agora usa banco de dados SQL")
        print("   2. Você pode manter o arquivo users.json como backup")
        print("   3. Todos os novos usuários serão salvos no banco de dados")
        print("   4. Reinicie o servidor para garantir que está usando o banco de dados")
        print()
    else:
        print("⚠️  Nenhum usuário foi migrado.")
        print("   Isso pode ser normal se:")
        print("   - O arquivo users.json estava vazio")
        print("   - Todos os usuários já estavam no banco de dados")
        print()
    
    if errors:
        print("⚠️  ERROS ENCONTRADOS:")
        for error in errors:
            print(f"   - {error}")
        print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migração cancelada pelo usuário.")
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

