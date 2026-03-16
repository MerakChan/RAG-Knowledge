import pymysql
from sqlalchemy import create_engine, inspect, text
from urllib.parse import quote_plus

class SQLService:
    def get_connection_url(self, db_type, host, port, user, password, db_name):
        if db_type == 'mysql':
            password = quote_plus(password)
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4"
        raise ValueError(f"Unsupported database type: {db_type}")

    def test_connection(self, db_type, host, port, user, password, db_name):
        try:
            url = self.get_connection_url(db_type, host, port, user, password, db_name)
            engine = create_engine(url)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    def get_schema(self, db_type, host, port, user, password, db_name):
        try:
            url = self.get_connection_url(db_type, host, port, user, password, db_name)
            engine = create_engine(url)
            inspector = inspect(engine)
            
            structured_schema = []
            
            table_names = inspector.get_table_names()
            
            for table in table_names:
                columns = inspector.get_columns(table)
                pk_constraint = inspector.get_pk_constraint(table)
                pk_cols = pk_constraint.get('constrained_columns', [])
                
                for col in columns:
                    structured_schema.append({
                        'table_name': table,
                        'column_name': col['name'],
                        'column_type': str(col['type']),
                        'column_comment': col.get('comment'),
                        'is_primary_key': 1 if col['name'] in pk_cols else 0
                    })
                
            return structured_schema
        except Exception as e:
            raise Exception(f"Failed to get schema: {str(e)}")

    def get_schema_text(self, db_type, host, port, user, password, db_name):
        # 兼容旧逻辑，返回文本格式
        try:
            structured_schema = self.get_schema(db_type, host, port, user, password, db_name)
            
            schema_map = {}
            for item in structured_schema:
                table = item['table_name']
                if table not in schema_map:
                    schema_map[table] = []
                schema_map[table].append(f"{item['column_name']} {item['column_type']}")
            
            schema_info = []
            for table, cols in schema_map.items():
                schema_info.append(f"Table {table}\n" + "\n".join(cols))
                
            return "\n\n".join(schema_info)
        except Exception as e:
            raise Exception(f"Failed to get schema text: {str(e)}")

    def execute_query(self, db_type, host, port, user, password, db_name, sql):
        try:
            # 安全检查：仅允许 SELECT
            if not sql.strip().upper().startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed for safety.")
                
            url = self.get_connection_url(db_type, host, port, user, password, db_name)
            engine = create_engine(url)
            with engine.connect() as connection:
                result = connection.execute(text(sql))
                keys = result.keys()
                data = [dict(zip(keys, row)) for row in result.fetchall()]
                return {
                    'columns': list(keys),
                    'data': data
                }
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
