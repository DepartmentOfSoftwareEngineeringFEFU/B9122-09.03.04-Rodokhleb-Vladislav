import re
from typing import List, Optional
from functools import lru_cache


class TextProcessor:


    def __init__(self, use_cache: bool = True, add_article: bool = True):
        self.use_cache = use_cache
        self.add_article = add_article
        self._translator = None
        self._translator_type = None
        self._init_translator()

    def _init_translator(self):
        try:
            from deep_translator import GoogleTranslator
            self._translator = GoogleTranslator(source='ru', target='en')
            self._translator_type = 'deep-translator'
            print("Инициализирован переводчик deep-translator")
            return
        except ImportError:
            pass

        try:
            from googletrans import Translator
            self._translator = Translator()
            self._translator_type = 'googletrans'
            print("Инициализирован переводчик googletrans")
        except ImportError:
            print("Переводчики не установлены. Будет использован fallback-режим.")
            self._translator = None
            self._translator_type = 'none'

    def is_english(self, text: str) -> bool:
        if not text:
            return True
        return not bool(re.search('[а-яА-ЯёЁ]', text))

    def _add_article(self, text: str) -> str:
        if not self.add_article:
            return text

        text = text.strip().lower()
        if not text:
            return text

        first_word = text.split()[0] if ' ' in text else text

        if first_word in ['a', 'an', 'the']:
            return text

        if ' ' in text:
            return text

        return f"a {text}"

    async def _translate_async(self, text: str) -> str:
        if self._translator_type == 'googletrans':
            result = await self._translator.translate(text, src='ru', dest='en')
            return result.text
        return text

    @lru_cache(maxsize=1000)
    def _translate_cached(self, text: str) -> str:
        if self._translator is None:
            return text

        try:
            if self._translator_type == 'deep-translator':
                translated = self._translator.translate(text)
            elif self._translator_type == 'googletrans':
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                translated = loop.run_until_complete(self._translate_async(text))
                loop.close()
            else:
                return text
            return self._add_article(translated)

        except Exception as e:
            print(f"Ошибка перевода '{text}': {e}")
            return text

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return text

        if self.is_english(text):
            return self._add_article(text.lower().strip())

        if self.use_cache:
            return self._translate_cached(text.strip())
        else:
            if self._translator is None:
                return text
            try:
                if self._translator_type == 'deep-translator':
                    translated = self._translator.translate(text.strip())
                elif self._translator_type == 'googletrans':
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    translated = loop.run_until_complete(self._translate_async(text.strip()))
                    loop.close()
                else:
                    return text

                return self._add_article(translated)
            except Exception as e:
                print(f"Ошибка перевода '{text}': {e}")
                return text

    def translate_batch(self, texts: List[str]) -> List[str]:
        return [self.translate(t) for t in texts]

    def prepare_prompt(self, keyword: str) -> str:
        if not keyword or not keyword.strip():
            return keyword

        result = self.translate(keyword)
        return result

    def prepare_prompts(self, keywords: List[str]) -> List[str]:
        return [self.prepare_prompt(kw) for kw in keywords]

    def prepare_for_detector(self, keywords: List[str]) -> List[str]:
        prepared = self.prepare_prompts(keywords)
        return [kw + '.' if not kw.endswith('.') else kw for kw in prepared]