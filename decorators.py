import functools
import logging
from typing import Type, Union, Tuple, Any

def safe_execute(
    default_return: Any = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_errors: bool = True,
    reraise: bool = False
):
    """安全执行装饰器

    Args:
        default_return: 异常时返回的默认值
        exceptions: 要捕获的异常类型
        log_errors: 是否记录错误日志
        reraise: 是否重新抛出异常

    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    logging.error(f"Function {func.__name__} failed: {e}")
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator

def async_safe_execute(
    default_return: Any = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_errors: bool = True,
    reraise: bool = False
):
    """异步安全执行装饰器

    Args:
        default_return: 异常时返回的默认值
        exceptions: 要捕获的异常类型
        log_errors: 是否记录错误日志
        reraise: 是否重新抛出异常

    Returns:
        异步装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    logging.error(f"Async function {func.__name__} failed: {e}")
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_errors: bool = True
):
    """重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 要重试的异常类型
        log_errors: 是否记录错误日志

    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if log_errors:
                            logging.warning(f"Function {func.__name__} attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                        import time
                        time.sleep(delay)
                    else:
                        if log_errors:
                            logging.error(f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}")

            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception
        return wrapper
    return decorator

def validate_arguments(**validators):
    """参数验证装饰器

    Args:
        validators: 参数验证器字典，格式为 {参数名: 验证函数}

    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数参数名
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 验证每个参数
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Parameter {param_name} validation failed: {value}")

            return func(*args, **kwargs)
        return wrapper
    return decorator