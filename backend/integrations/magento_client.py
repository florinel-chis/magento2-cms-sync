import httpx
from typing import List, Dict, Any, Optional
import asyncio
from urllib.parse import urljoin
import json

from config import settings


class MagentoClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Any:
        url = urljoin(f"{self.base_url}/rest/V1/", endpoint.lstrip('/'))
        
        async with httpx.AsyncClient(timeout=settings.magento_timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                    params=params
                )
                response.raise_for_status()
                
                if response.content:
                    return response.json()
                return None
                
            except httpx.HTTPStatusError as e:
                if retry_count < settings.magento_retry_attempts and e.response.status_code >= 500:
                    await asyncio.sleep(settings.magento_retry_delay * (retry_count + 1))
                    return await self._make_request(method, endpoint, json_data, params, retry_count + 1)
                raise
            except httpx.RequestError as e:
                if retry_count < settings.magento_retry_attempts:
                    await asyncio.sleep(settings.magento_retry_delay * (retry_count + 1))
                    return await self._make_request(method, endpoint, json_data, params, retry_count + 1)
                raise
    
    async def get_store_views(self) -> List[Dict[str, Any]]:
        """Get all store views"""
        return await self._make_request("GET", "store/storeViews")
    
    async def get_cms_blocks(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get all CMS blocks"""
        all_blocks = []
        current_page = 1
        
        while True:
            params = {
                "searchCriteria[pageSize]": page_size,
                "searchCriteria[currentPage]": current_page
            }
            
            result = await self._make_request("GET", "cmsBlock/search", params=params)
            
            if not result or "items" not in result:
                break
                
            all_blocks.extend(result["items"])
            
            # Check if there are more pages
            total_count = result.get("total_count", 0)
            if len(all_blocks) >= total_count:
                break
                
            current_page += 1
            
        return all_blocks
    
    async def get_cms_pages(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get all CMS pages"""
        all_pages = []
        current_page = 1
        
        while True:
            params = {
                "searchCriteria[pageSize]": page_size,
                "searchCriteria[currentPage]": current_page
            }
            
            result = await self._make_request("GET", "cmsPage/search", params=params)
            
            if not result or "items" not in result:
                break
                
            all_pages.extend(result["items"])
            
            # Check if there are more pages
            total_count = result.get("total_count", 0)
            if len(all_pages) >= total_count:
                break
                
            current_page += 1
            
        return all_pages
    
    async def get_cms_block(self, block_id: int) -> Dict[str, Any]:
        """Get a single CMS block by ID"""
        return await self._make_request("GET", f"cmsBlock/{block_id}")
    
    async def get_cms_page(self, page_id: int) -> Dict[str, Any]:
        """Get a single CMS page by ID"""
        return await self._make_request("GET", f"cmsPage/{page_id}")
    
    async def create_cms_block(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new CMS block"""
        return await self._make_request("POST", "cmsBlock", {"block": block_data})
    
    async def create_cms_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new CMS page"""
        return await self._make_request("POST", "cmsPage", {"page": page_data})
    
    async def update_cms_block(self, block_id: int, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing CMS block"""
        return await self._make_request("PUT", f"cmsBlock/{block_id}", {"block": block_data})
    
    async def update_cms_page(self, page_id: int, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing CMS page"""
        return await self._make_request("PUT", f"cmsPage/{page_id}", {"page": page_data})