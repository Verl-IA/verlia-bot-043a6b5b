import aiohttp
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

"""Verl.ia Database Manager - Auto-configured"""

log = logging.getLogger('bot')

class Database:
    """Gerenciador de banco de dados Verl.ia"""
    
    def __init__(self):
        self.url = os.environ.get('VERLIA_DB_ENDPOINT', "https://amqhmgatgweklzvcfdiy.supabase.co/functions/v1/bot-webhook")
        self.bot_id = os.environ.get('BOT_ID', '043a6b5b-a2f1-4812-bd92-dfe68e69f56a')
    
    async def _call(self, action: str, db_name: str, data: Dict = None, filters: Dict = None) -> Dict | List[Dict]:
        """Método interno para fazer chamadas à API do banco de dados."""
        payload = {
            "action": action,
            "database": db_name,
            "bot_id": self.bot_id,
        }
        if data:
            payload["data"] = data
        if filters:
            payload["filters"] = filters

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.url}/database", json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            log.error(f"Erro de conexão com o DB ({action} {db_name}): {e}")
            return {"error": str(e)}
        except Exception as e:
            log.error(f"Erro inesperado no DB ({action} {db_name}): {e}")
            return {"error": str(e)}
    
    async def save(self, db_name: str, data: Dict) -> Dict:
        """Salva um novo registro no banco de dados."""
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        response = await self._call("insert", db_name, data=data)
        if response and "error" in response:
            log.error(f"Erro ao salvar em '{db_name}': {response.get('error')}")
            return {"error": response["error"]}
        return response
    
    async def get(self, db_name: str, filters: Dict = None) -> List[Dict]:
        """Obtém múltiplos registros do banco de dados."""
        response = await self._call("select", db_name, filters=filters)
        if response and "error" in response:
            log.error(f"Erro ao obter de '{db_name}': {response.get('error')}")
            return []
        return response.get("data", []) if response else []
    
    async def get_one(self, db_name: str, filters: Dict) -> Optional[Dict]:
        """Obtém um único registro do banco de dados."""
        data = await self.get(db_name, filters)
        return data[0] if data else None
    
    async def update(self, db_name: str, filters: Dict, data: Dict) -> Dict:
        """Atualiza registros existentes no banco de dados."""
        if not filters:
            return {"error": "Update requires filters"}
        response = await self._call("update", db_name, data=data, filters=filters)
        if response and "error" in response:
            return {"error": response["error"]}
        return response
    
    async def delete(self, db_name: str, filters: Dict) -> Dict:
        """Deleta registros do banco de dados."""
        if not filters:
            return {"error": "Delete requires filters"}
        response = await self._call("delete", db_name, filters=filters)
        if response and "error" in response:
            return {"error": response["error"]}
        return response
    
    async def count(self, db_name: str, filters: Dict = None) -> int:
        """Conta o número de registros no banco de dados."""
        response = await self._call("count", db_name, filters=filters)
        if response and "error" in response:
            return 0
        return response.get("count", 0) if response else 0


# Instância global do database
db = Database()
