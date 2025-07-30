import importlib
import inspect
import os
import grpc
from typing import Any, Optional
from pybantic.convert import convert_to_protobuf, convert_from_protobuf


class gRPCClient:  # 修复拼写错误
    """动态 gRPC 客户端适配器"""

    def __init__(
        self,
        service,
        target: str,
        credentials: Optional[grpc.ChannelCredentials] = None,
    ):
        """
        Args:
            service: 用 @pb.service 装饰的服务类
            target: 服务器地址 (如 'localhost:50051')
            credentials: gRPC 凭证，None 表示不安全连接
        """
        self.service = service
        self.target = target

        # 创建 gRPC 通道
        if credentials:
            self.channel = grpc.secure_channel(target, credentials)
        else:
            self.channel = grpc.insecure_channel(target)

        # 动态创建 stub 实例
        self.stub = self._create_stub()

    def _create_stub(self):
        """动态创建 gRPC stub 实例"""
        # 根据服务类文件推断模块名
        source_file = inspect.getfile(self.service)
        filename = os.path.splitext(os.path.basename(source_file))[0]
        grpc_module_name = f"{filename}_pb2_grpc"

        try:
            # 导入 gRPC 模块
            grpc_module = importlib.import_module(grpc_module_name)
            # 获取 stub 类
            stub_class = getattr(grpc_module, f"{self.service.__name__}Stub")
            # 创建 stub 实例
            return stub_class(self.channel)
        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"无法创建 gRPC stub: {e}")

    def __getattr__(self, name: str) -> Any:
        """动态拦截方法调用，自动处理转换"""
        # 检查服务类是否有这个方法
        if not hasattr(self.service, name):
            raise AttributeError(f"服务 {self.service.__name__} 没有方法 {name}")

        # 获取服务类的方法（用于类型信息）
        annotated_method = getattr(self.service, name)

        # 检查是否是被 expose 装饰的方法
        if not (
            hasattr(annotated_method, "__pybantic_type__")
            and annotated_method.__pybantic_type__ == "method"
        ):
            raise AttributeError(f"方法 {name} 未被 @expose 装饰")

        # 获取原生 gRPC 方法（首字母大写，符合 gRPC 约定）
        grpc_method_name = name
        if not hasattr(self.stub, grpc_method_name):
            raise AttributeError(f"gRPC stub 没有方法 {grpc_method_name}")

        original_method = getattr(self.stub, grpc_method_name)

        # 提取类型注解
        signature = inspect.signature(annotated_method)
        parameters = list(signature.parameters.values())
        request_type = parameters[1].annotation  # 跳过 self 参数
        response_type = signature.return_annotation

        def wrapper(request, **kwargs):
            """自动转换的包装方法"""
            try:
                # pydantic -> protobuf
                request_pb = convert_to_protobuf(request)
                print(request_pb)

                # 调用原生 gRPC 方法
                response_pb = original_method(request=request_pb, **kwargs)
                print(response_pb)

                # protobuf -> pydantic
                return convert_from_protobuf(response_type, response_pb)

            except Exception as e:
                raise RuntimeError(
                    f"调用 {self.service.__name__}.{name} 失败：{e}"
                ) from e

        # 保持方法的类型信息和文档
        wrapper.__name__ = name
        wrapper.__doc__ = f"调用 {self.service.__name__}.{name} 方法"
        wrapper.__annotations__ = {"request": request_type, "return": response_type}

        return wrapper

    def close(self):
        """关闭 gRPC 连接"""
        if hasattr(self, "channel"):
            self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便捷函数
def create_client(
    service_class, target: str, credentials: Optional[grpc.ChannelCredentials] = None
) -> gRPCClient:
    """
    便捷的客户端创建函数

    Args:
        service_class: 用 @pb.service 装饰的服务类
        target: 服务器地址 (如 'localhost:50051')
        credentials: gRPC 凭证

    Returns:
        配置好的客户端实例
    """
    return gRPCClient(service_class, target, credentials)
