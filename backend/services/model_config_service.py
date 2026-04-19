import copy
import json
import os
import re
import uuid

from config import Config


class ModelConfigService:
    def __init__(self, config_path=None):
        self.config_path = config_path or Config.MODEL_CONFIG_FILE
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

    def _default_config(self):
        return {
            "active_chat_model_id": "builtin-deepseek-chat",
            "active_embedding_model": "bge-large",
            "builtin_models": [
                {
                    "id": "builtin-deepseek-chat",
                    "name": "DeepSeek Chat",
                    "provider": "deepseek",
                    "model_name": "deepseek-chat",
                    "base_url": "https://api.deepseek.com/v1/chat/completions",
                    "api_key": Config.DEEPSEEK_API_KEY,
                    "source": "builtin",
                    "editable": False,
                    "description": "默认集成的 DeepSeek 通用对话模型，适合常规 RAG 问答场景。",
                    "type": "cloud",
                    "enabled": True,
                    "tags": ["推理强", "速度快", "通用对话"],
                    "auto_tags": ["通用对话", "知识库问答", "文本总结"]
                },
                {
                    "id": "builtin-deepseek-reasoner",
                    "name": "DeepSeek Reasoner",
                    "provider": "deepseek",
                    "model_name": "deepseek-reasoner",
                    "base_url": "https://api.deepseek.com/v1/chat/completions",
                    "api_key": Config.DEEPSEEK_API_KEY,
                    "source": "builtin",
                    "editable": False,
                    "description": "偏推理与复杂分析的 DeepSeek 模型，适合结构化推断场景。",
                    "type": "cloud",
                    "enabled": True,
                    "tags": ["推理强", "逻辑分析", "复杂任务"],
                    "auto_tags": ["逻辑推理", "复杂分析", "知识图谱构建"]
                },
            ],
            "custom_models": [],
            "embedding_options": [
                {"id": "bge-large", "name": "BGE Large", "description": "默认中文向量模型，适合通用知识库检索"},
                {"id": "bge-m3", "name": "BGE M3", "description": "支持多语言与多粒度召回的向量模型"},
                {"id": "text-embedding-3-large", "name": "Text Embedding 3 Large", "description": "OpenAI 兼容向量模型，可用于外部 API 接入"},
            ],
            "task_assignments": {
                "chat": "builtin-deepseek-chat",
                "rag": "builtin-deepseek-chat",
                "summary": "builtin-deepseek-chat",
                "knowledge_graph": "builtin-deepseek-reasoner",
                "multi_doc_analysis": "builtin-deepseek-reasoner",
                "knowledge_trace": "builtin-deepseek-chat"
            },
            "scheduling_strategy": "fixed",
            "fallback_models": {
                "builtin-deepseek-chat": ["builtin-deepseek-reasoner"],
                "builtin-deepseek-reasoner": ["builtin-deepseek-chat"]
            }
        }

    def _merge_builtin_models(self, config):
        default_builtins = {
            item["id"]: item
            for item in self._default_config()["builtin_models"]
        }
        merged = []
        existing_ids = set()

        for current in config.get("builtin_models", []):
            model_id = current.get("id")
            base = copy.deepcopy(default_builtins.get(model_id, {}))
            merged_model = {**base, **current}

            if not merged_model.get("api_key") and base.get("api_key"):
                merged_model["api_key"] = base["api_key"]
            if not merged_model.get("base_url") and base.get("base_url"):
                merged_model["base_url"] = base["base_url"]
            if not merged_model.get("model_name") and base.get("model_name"):
                merged_model["model_name"] = base["model_name"]
            if "type" not in merged_model and base.get("type"):
                merged_model["type"] = base["type"]
            if "enabled" not in merged_model and "enabled" in base:
                merged_model["enabled"] = base["enabled"]
            if "tags" not in merged_model and base.get("tags"):
                merged_model["tags"] = base["tags"]
            if "auto_tags" not in merged_model and base.get("auto_tags"):
                merged_model["auto_tags"] = base["auto_tags"]

            merged.append(merged_model)
            if model_id:
                existing_ids.add(model_id)

        for model_id, builtin in default_builtins.items():
            if model_id not in existing_ids:
                merged.append(copy.deepcopy(builtin))

        config["builtin_models"] = merged
        return config

    def _read(self):
        if not os.path.exists(self.config_path):
            config = self._default_config()
            self._write(config)
            return config

        with open(self.config_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        default_config = self._default_config()
        data.setdefault("active_chat_model_id", default_config["active_chat_model_id"])
        data.setdefault("active_embedding_model", default_config["active_embedding_model"])
        data.setdefault("builtin_models", default_config["builtin_models"])
        data.setdefault("custom_models", [])
        data.setdefault("embedding_options", default_config["embedding_options"])
        data.setdefault("task_assignments", default_config["task_assignments"])
        data.setdefault("scheduling_strategy", default_config["scheduling_strategy"])
        data.setdefault("fallback_models", default_config["fallback_models"])
        data = self._merge_builtin_models(data)
        return data

    def _write(self, data):
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    @staticmethod
    def normalize_base_url(value):
        raw = str(value or "").strip()
        if not raw:
            return ""

        match = re.search(r"https?://\S+", raw)
        if match:
            return match.group(0).rstrip(" ,;)")
        return raw

    @staticmethod
    def normalize_model_name(value, provider="", base_url=""):
        raw = str(value or "").strip()
        if not raw:
            return ""

        provider_text = str(provider or "").strip().lower()
        normalized_base_url = ModelConfigService.normalize_base_url(base_url).lower()
        compact = re.sub(r"[\s_]+", "-", raw.lower())

        if (
            provider_text in {"xunfei", "spark", "xfyun"}
            or "spark-api-open.xf-yun.com" in normalized_base_url
            or "xf-yun.com" in normalized_base_url
        ):
            if compact in {"spark-x", "sparkx", "x2", "spark-x2", "spark-x-2"}:
                return "spark-x"

        return raw

    def _mask_model(self, model):
        masked = copy.deepcopy(model)
        masked["base_url"] = self.normalize_base_url(masked.get("base_url"))
        masked["model_name"] = self.normalize_model_name(
            masked.get("model_name"),
            masked.get("provider"),
            masked.get("base_url"),
        )
        api_key = masked.get("api_key") or ""
        masked["has_api_key"] = bool(api_key)
        masked["api_key_preview"] = f"{api_key[:4]}***{api_key[-4:]}" if len(api_key) >= 8 else ""
        masked.pop("api_key", None)
        return masked

    def list_models(self):
        config = self._read()
        models = [self._mask_model(item) for item in config["builtin_models"] + config["custom_models"]]
        return {
            "active_chat_model_id": config["active_chat_model_id"],
            "active_embedding_model": config["active_embedding_model"],
            "embedding_options": config["embedding_options"],
            "models": models,
        }

    def get_runtime_chat_model(self):
        config = self._read()
        active_id = config["active_chat_model_id"]
        for model in config["builtin_models"] + config["custom_models"]:
            if model["id"] == active_id:
                model["base_url"] = self.normalize_base_url(model.get("base_url"))
                model["model_name"] = self.normalize_model_name(
                    model.get("model_name"),
                    model.get("provider"),
                    model.get("base_url"),
                )
                if model.get("api_key") or model.get("source") != "builtin":
                    return model
                break

        for model in config["builtin_models"]:
            model["base_url"] = self.normalize_base_url(model.get("base_url"))
            model["model_name"] = self.normalize_model_name(
                model.get("model_name"),
                model.get("provider"),
                model.get("base_url"),
            )
            if model.get("api_key"):
                return model
        fallback_model = config["builtin_models"][0]
        fallback_model["base_url"] = self.normalize_base_url(fallback_model.get("base_url"))
        fallback_model["model_name"] = self.normalize_model_name(
            fallback_model.get("model_name"),
            fallback_model.get("provider"),
            fallback_model.get("base_url"),
        )
        return fallback_model

    def save_custom_model(self, payload):
        config = self._read()
        model_id = payload.get("id")
        custom_models = config["custom_models"]
        existing = next((item for item in custom_models if item["id"] == model_id), None) if model_id else None

        model_data = {
            "id": existing["id"] if existing else f"custom-{uuid.uuid4().hex[:10]}",
            "name": payload["name"].strip(),
            "provider": payload.get("provider", "openai-compatible").strip(),
            "model_name": self.normalize_model_name(
                payload["model_name"],
                payload.get("provider", "openai-compatible"),
                payload["base_url"],
            ),
            "base_url": self.normalize_base_url(payload["base_url"]),
            "api_key": payload.get("api_key", "").strip() or (existing.get("api_key", "") if existing else ""),
            "source": "custom",
            "editable": True,
            "description": payload.get("description", "").strip() or "用户自定义接入的 OpenAI 兼容模型 API。",
            "type": payload.get("type", "cloud"),
            "enabled": payload.get("enabled", True) if existing is None else existing.get("enabled", True),
            "tags": payload.get("tags", []) if existing is None else existing.get("tags", []),
            "auto_tags": payload.get("auto_tags", []) if existing is None else existing.get("auto_tags", []),
        }

        if existing:
            existing.update(model_data)
        else:
            custom_models.append(model_data)

        if payload.get("set_active"):
            config["active_chat_model_id"] = model_data["id"]

        self._write(config)
        return self.list_models()

    def activate_model(self, model_id):
        config = self._read()
        all_ids = {item["id"] for item in config["builtin_models"] + config["custom_models"]}
        if model_id not in all_ids:
            raise ValueError("Model not found")
        config["active_chat_model_id"] = model_id
        self._write(config)
        return self.list_models()

    def set_embedding_model(self, embedding_model_id):
        config = self._read()
        valid_ids = {item["id"] for item in config["embedding_options"]}
        if embedding_model_id not in valid_ids:
            raise ValueError("Embedding model not found")
        config["active_embedding_model"] = embedding_model_id
        self._write(config)
        return self.list_models()

    def delete_custom_model(self, model_id):
        config = self._read()
        custom_models = config["custom_models"]
        remaining = [item for item in custom_models if item["id"] != model_id]
        if len(remaining) == len(custom_models):
            raise ValueError("Custom model not found")

        config["custom_models"] = remaining
        if config["active_chat_model_id"] == model_id:
            config["active_chat_model_id"] = config["builtin_models"][0]["id"]

        self._write(config)
        return self.list_models()

    def update_model_status(self, model_id, enabled):
        config = self._read()
        all_models = config["builtin_models"] + config["custom_models"]
        for model in all_models:
            if model["id"] == model_id:
                model["enabled"] = enabled
                break
        self._write(config)
        return self.list_models()

    def update_model_tags(self, model_id, tags):
        config = self._read()
        all_models = config["builtin_models"] + config["custom_models"]
        for model in all_models:
            if model["id"] == model_id:
                model["tags"] = tags or []
                break
        self._write(config)
        return self.list_models()

    def update_model_type(self, model_id, model_type):
        config = self._read()
        all_models = config["builtin_models"] + config["custom_models"]
        for model in all_models:
            if model["id"] == model_id:
                model["type"] = model_type
                break
        self._write(config)
        return self.list_models()

    def get_task_assignments(self):
        config = self._read()
        return {
            "task_assignments": config.get("task_assignments", {}),
            "scheduling_strategy": config.get("scheduling_strategy", "fixed"),
            "fallback_models": config.get("fallback_models", {})
        }

    def update_task_assignment(self, task_type, model_id):
        config = self._read()
        if "task_assignments" not in config:
            config["task_assignments"] = {}
        config["task_assignments"][task_type] = model_id
        self._write(config)
        return self.get_task_assignments()

    def update_scheduling_strategy(self, strategy):
        if strategy not in ["fixed", "tag", "fallback"]:
            raise ValueError("Invalid scheduling strategy")
        config = self._read()
        config["scheduling_strategy"] = strategy
        self._write(config)
        return self.get_task_assignments()

    def update_fallback_models(self, model_id, fallback_ids):
        config = self._read()
        if "fallback_models" not in config:
            config["fallback_models"] = {}
        config["fallback_models"][model_id] = fallback_ids or []
        self._write(config)
        return self.get_task_assignments()

    def get_model_for_task(self, task_type):
        config = self._read()
        strategy = config.get("scheduling_strategy", "fixed")
        task_assignments = config.get("task_assignments", {})
        fallback_models = config.get("fallback_models", {})
        all_models = config["builtin_models"] + config["custom_models"]
        
        if strategy == "fixed":
            model_id = task_assignments.get(task_type)
            if model_id:
                model = next((m for m in all_models if m["id"] == model_id and m.get("enabled", True)), None)
                if model:
                    return model
                if fallback_models.get(model_id):
                    for fallback_id in fallback_models[model_id]:
                        fallback = next((m for m in all_models if m["id"] == fallback_id and m.get("enabled", True)), None)
                        if fallback:
                            return fallback
        
        elif strategy == "tag":
            task_tag_map = {
                "chat": "通用对话",
                "rag": "知识库问答",
                "summary": "文本总结",
                "knowledge_graph": "知识图谱构建",
                "multi_doc_analysis": "复杂分析",
                "knowledge_trace": "知识库问答"
            }
            target_tag = task_tag_map.get(task_type)
            if target_tag:
                for model in all_models:
                    if model.get("enabled", True):
                        all_tags = (model.get("tags", []) + model.get("auto_tags", []))
                        if target_tag in all_tags:
                            return model
        
        enabled_models = [m for m in all_models if m.get("enabled", True)]
        if enabled_models:
            return enabled_models[0]
        return all_models[0]
