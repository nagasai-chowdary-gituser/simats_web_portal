import sys
from src.logger import logging
def error_message_detail(error,error_detail:sys):
    _,_,exc_tb=error_detail.exc_info()
    filename=exc_tb.tb_frame.f_code.co_filename
    error_message=f"the error in the file [{0}], in the line [{1}], the error is [{2}]".format(filename,exc_tb.tb_lineno,str(error))
    return error_message
class CustomException:
    def __init__(self,error_message,error_details:sys):
        super.__init__(error_message)
        self.error_message=error_message_detail(error_message,error_detail=error_details)
        def __str__(self):
            return self.error_message
if __name__=="__main__":
    try:
        a=1/0
    except CustomException as e:
        logging.info("error occured")
        raise CustomException(e,sys)
        