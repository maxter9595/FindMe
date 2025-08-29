import os
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

os.environ['DB_NAME'] = 'test_db'
os.environ['USER_NAME_DB'] = 'test_user'
os.environ['USER_PASSWORD_DB'] = 'test_password'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['VK_GROUP_TOKEN'] = 'vk_group_token'
os.environ['VK_USER_TOKEN'] = 'vk_user_token'
