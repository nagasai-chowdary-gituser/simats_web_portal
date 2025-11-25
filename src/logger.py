import logging
import os
from datetime import datetime
log_file_name=f"{datetime.now().strftime('%d_%m_%y_%H_%M_%S')}.log"
log_path=os.path.join(os.getcwd(),'logss')
os.makedirs(log_path,exist_ok=True)
log_filename=os.path.join(log_path,log_file_name)
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="[%(asctime)s %(lineno)d %(name)s %(levelname)s %(message)s]"
)