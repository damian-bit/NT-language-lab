"""
Cliente HTTP para el backend LLM (llama.cpp con API tipo OpenAI).
Conecta a un servidor que expone /v1/chat/completions (p. ej. http://host.docker.internal:8080).
"""
import os
import requests
from typing import Optional


class LLMClient:
    """
    Cliente para comunicarse con un servidor llama.cpp vía HTTP (API compatible OpenAI).
    Configuración vía variables de entorno: LLM_BASE_URL, LLM_MODEL.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Inicializa el cliente del LLM.

        Args:
            base_url: URL base del servidor (sin trailing slash). Por defecto LLM_BASE_URL
                      o http://host.docker.internal:8080
            model: Nombre del modelo en el servidor. Por defecto LLM_MODEL o Phi-3 Mini Instruct
        """
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL") or "http://host.docker.internal:8080").rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL", "Phi-3 Mini Instruct")
        self.chat_url = f"{self.base_url}/v1/chat/completions"
        self.timeout = 120

    def generate(self, prompt: str, context: str) -> str:
        """
        Genera una respuesta usando el LLM con el contexto proporcionado.
        Mantiene el mismo contrato y semántica que la capa anterior (RAG estricto).

        Args:
            prompt: Prompt para el modelo (instrucción de comparación).
            context: Contexto (versículo recuperado) a usar para la comparación.

        Returns:
            Respuesta del modelo como texto.
        """
        # Lo que sigue es el texto real que recibe el LLM (no es documentación)
        full_prompt = f"""Eres un experto en lingüística comparativa especializado en griego koiné y español.

CONTEXTO (usa SOLO este texto):
{context}

INSTRUCCIONES:
- Realiza una comparación LINGÜÍSTICA (no teológica)
- Analiza palabras clave, matices de traducción y estructura gramatical
- Cita siempre el libro, capítulo y versículo
- Indica claramente el idioma de cada texto
- Explica que el griego es el texto original
- Si el contexto no contiene el versículo solicitado, indica que no se encontró

{prompt}"""

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": False,
        }

        try:
            resp = requests.post(
                self.chat_url,
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            # API tipo OpenAI: choices[0].message.content
            choices = data.get("choices") or []
            if choices and isinstance(choices[0].get("message"), dict):
                return (choices[0]["message"].get("content") or "").strip()
            if choices and isinstance(choices[0], dict) and "message" in choices[0]:
                return (choices[0]["message"].get("content") or "").strip()
            return str(data)
        except requests.exceptions.RequestException as e:
            return (
                f"Error al generar respuesta: {e}\n\n"
                f"Asegúrate de que:\n"
                f"1. El servidor llama.cpp esté corriendo en el host\n"
                f"2. El endpoint {self.chat_url} sea accesible desde el contenedor\n"
                f"3. Las variables LLM_BASE_URL y LLM_MODEL estén configuradas si usas valores distintos"
            )
