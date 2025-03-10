from typing import Optional, Dict, Any, List
from langchain.schema.runnable import Runnable
from chatbot.utils import store_articles_custom_range, store_daily_articles
from chatbot.fetchArticles import store_multilingual_daily_articles, store_multilingual_articles_custom_range



class StoreMultilingualDailyArticles(Runnable):
    """
    A class to fetch and store multilingual articles for the current day.
    Supports English, Hindi, and Bengali languages.
    """
    async def invoke(self, lang: str = "en", *args, **kwargs) -> Dict[str, Any]:
        """
        Fetch and store articles for the current day asynchronously in the specified language.

        Args:
            lang (str): Language code - "en" (English), "hi" (Hindi), or "bn" (Bengali).
                       Defaults to "en".

        Returns:
            dict: A dictionary containing the status and details of the operation.
        """
        try:
            # Validate language parameter
            if lang not in ["en", "hi", "bn"]:
                return {
                    "status": "error",
                    "message": f"Unsupported language code: {lang}. Supported codes are 'en', 'hi', and 'bn'."
                }
            
            # Fetch and store articles for today in the specified language
            daily_articles = await store_multilingual_daily_articles(lang=lang)
            
            # Return success response
            return {
                "status": "success",
                "message": f"Articles for today in {self._get_language_name(lang)} have been successfully stored.",
                "language": self._get_language_name(lang),
                "language_code": lang,
                "details": daily_articles,
            }
        except Exception as e:
            # Handle any errors
            return {
                "status": "error",
                "message": f"Failed to store daily articles in {self._get_language_name(lang)}.",
                "language": self._get_language_name(lang),
                "language_code": lang,
                "error": str(e),
            }
    
    def _get_language_name(self, lang_code: str) -> str:
        """
        Convert language code to full language name.
        
        Args:
            lang_code (str): Language code.
            
        Returns:
            str: Full language name.
        """
        language_map = {
            "en": "English",
            "hi": "Hindi",
            "bn": "Bengali"
        }
        return language_map.get(lang_code, "Unknown")


class StoreMultilingualCustomRangeArticles(Runnable):
    """
    A class to fetch and store multilingual articles within a custom date range.
    Supports English, Hindi, and Bengali languages.
    """
    async def invoke(self, 
                    from_date: Optional[str] = None, 
                    to_date: Optional[str] = None, 
                    lang: str = "en", 
                    *args, **kwargs) -> Dict[str, Any]:
        """
        Fetch and store articles within a custom date range asynchronously in the specified language.

        Args:
            from_date (str, optional): Start date in 'YYYY-MM-DD' format. Defaults to 6 months ago.
            to_date (str, optional): End date in 'YYYY-MM-DD' format. Defaults to today.
            lang (str): Language code - "en" (English), "hi" (Hindi), or "bn" (Bengali).
                       Defaults to "en".

        Returns:
            dict: A dictionary containing the status and details of the operation.
        """
        try:
            # Validate language parameter
            if lang not in ["en", "hi", "bn"]:
                return {
                    "status": "error",
                    "message": f"Unsupported language code: {lang}. Supported codes are 'en', 'hi', and 'bn'."
                }
            
            # Call the function to store articles with the custom range in the specified language
            custom_range_articles = await store_multilingual_articles_custom_range(from_date, to_date, lang=lang)
            
            # If the operation is successful, return a success message
            return {
                "status": "success",
                "message": f"Articles from {from_date or '6 months ago'} to {to_date or 'today'} in {self._get_language_name(lang)} have been successfully stored.",
                "language": self._get_language_name(lang),
                "language_code": lang,
                "details": custom_range_articles,
            }
        except Exception as e:
            # Handle and log any errors that occur during the process
            return {
                "status": "error",
                "message": f"Failed to store articles in {self._get_language_name(lang)}.",
                "language": self._get_language_name(lang),
                "language_code": lang,
                "error": str(e),
            }
    
    def _get_language_name(self, lang_code: str) -> str:
        """
        Convert language code to full language name.
        
        Args:
            lang_code (str): Language code.
            
        Returns:
            str: Full language name.
        """
        language_map = {
            "en": "English",
            "hi": "Hindi",
            "bn": "Bengali"
        }
        return language_map.get(lang_code, "Unknown")

class StoreDailyArticles(Runnable):
    """
    A class to fetch and store articles for the current day.
    """
    async def invoke(self, *args, **kwargs):
        """
        Fetch and store articles for the current day asynchronously.

        Returns:
            dict: A dictionary containing the status and details of the operation.
        """
        try:
            # Fetch and store articles for today
            daily_articles = await store_daily_articles()
            
            # Return success response
            return {
                "status": "success",
                "message": "Articles for today have been successfully stored.",
                "details": daily_articles,
            }
        except Exception as e:
            # Handle any errors
            return {
                "status": "error",
                "message": "Failed to store daily articles.",
                "error": str(e),
            }






class StoreCustomRangeArticles(Runnable):
    """
    A class to fetch and store articles within a custom date range.
    """
    async def invoke(self, from_date: Optional[str] = None, to_date: Optional[str] = None, *args, **kwargs):
        """
        Fetch and store articles within a custom date range asynchronously.

        Args:
            from_date (str, optional): Start date in 'YYYY-MM-DD' format.
            to_date (str, optional): End date in 'YYYY-MM-DD' format.

        Returns:
            dict: A dictionary containing the status and details of the operation.
        """
        try:
            # Call the function to store articles with the custom range
            custom_range_articles = await store_articles_custom_range(from_date, to_date)
            
            # If the operation is successful, return a success message
            return {
                "status": "success",
                "message": f"Articles from {from_date or '6 months ago'} to {to_date or 'today'} have been successfully stored.",
                "details": custom_range_articles,
            }
        except Exception as e:
            # Handle and log any errors that occur during the process
            return {
                "status": "error",
                "message": "Failed to store articles.",
                "error": str(e),
            }




