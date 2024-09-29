import os
import aiohttp
import asyncio

class AsyncGitHubDownloader:
    GITHUB_API_URL = "https://api.github.com/repos"

    def __init__(self, repo_owner, repo_name, branch='main'):
        """
        Initialize the AsyncGitHubDownloader with repository information.

        Parameters:
        - repo_owner: str, the owner of the repository.
        - repo_name: str, the name of the repository.
        - branch: str, the branch of the repository (default is 'main').
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch

    async def _fetch(self, session, url):
        """
        Asynchronously fetch data from the given URL.
        
        Parameters:
        - session: aiohttp.ClientSession, the session to use for making requests.
        - url: str, the URL to fetch.

        Returns:
        - JSON response data.
        """
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to fetch data: {response.status}")

    async def _download_file(self, session, url, dest_folder, filename):
        """
        Asynchronously download a single file and save it to the destination folder.
        
        Parameters:
        - session: aiohttp.ClientSession, the session to use for downloading.
        - url: str, the file download URL.
        - dest_folder: str, the local folder where the file will be saved.
        - filename: str, the name of the file.
        """
        file_path = os.path.join(dest_folder, filename)
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                print(f"Downloaded {filename}")
            else:
                print(f"Failed to download {filename}: {response.status}")

    async def _get_folder_contents(self, session, folder_path):
        """
        Asynchronously fetch the contents of a folder in the repository.
        
        Parameters:
        - session: aiohttp.ClientSession, the session to use for making requests.
        - folder_path: str, the folder path inside the repository.

        Returns:
        - List of files and folders in the given path.
        """
        api_url = f"{self.GITHUB_API_URL}/{self.repo_owner}/{self.repo_name}/contents/{folder_path}?ref={self.branch}"
        return await self._fetch(session, api_url)

    async def download_folder(self, folder_path, dest_folder):
        """
        Asynchronously download all files from a specific folder in the repository.
        
        Parameters:
        - folder_path: str, the folder path inside the repository.
        - dest_folder: str, the local folder where files will be saved.
        """
        # Ensure the destination folder exists
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        # Start an aiohttp session
        async with aiohttp.ClientSession() as session:
            try:
                folder_contents = await self._get_folder_contents(session, folder_path)
            except Exception as e:
                print(str(e))
                return

            # Gather download tasks for all files in the folder
            tasks = []
            for item in folder_contents:
                if item['type'] == 'file':
                    download_url = item['download_url']
                    filename = item['name']
                    tasks.append(self._download_file(session, download_url, dest_folder, filename))

            # Run all download tasks concurrently
            await asyncio.gather(*tasks)
        print("All files downloaded successfully.")

# Example usage:
# async def main():
#     downloader = AsyncGitHubDownloader('octocat', 'Hello-World')
#     await downloader.download_folder('path/to/folder', './local_folder')

# asyncio.run(main())