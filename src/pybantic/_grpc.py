"""
简单的 from_protobuf 方法测试
"""
import typing
from google.protobuf import json_format
from google.protobuf.message import Message as ProtoMessage
from pydantic import BaseModel, ValidationError


class ProtobufMixin:
    @classmethod
    def from_protobuf(cls, protobuf: typing.Any):
        if not isinstance(protobuf, ProtoMessage):
            raise ValueError(f"Input must be a protobuf message, got {type(protobuf)}")
        
        # 将 protobuf 消息转换为字典
        json_dict = json_format.MessageToDict(
            protobuf, 
            preserving_proto_field_name=True,
            including_default_value_fields=True,
            use_integers_for_enums=True
        )
        
        # 预处理字典，处理特殊类型
        processed_dict = cls._prepare_protobuf_dict(json_dict)
        
        # 创建 Pydantic 模型实例
        try:
            instance = cls(**processed_dict)
            return instance
        except ValidationError as e:
            raise ValidationError(f"Failed to create {cls.__name__} from protobuf: {e}")
    
    @classmethod
    def _prepare_protobuf_dict(cls, json_dict: dict) -> dict:
        """
        预处理从 Protobuf 转换来的字典
        
        Args:
            json_dict: 从 Protobuf 转换的字典
            
        Returns:
            dict: 处理后的字典
        """
        processed_dict = {}
        
        for field_name, value in json_dict.items():
            if value is not None:
                processed_dict[field_name] = cls._convert_field_from_protobuf(field_name, value)
        
        return processed_dict
    
    @classmethod
    def _convert_field_from_protobuf(cls, field_name: str, value: typing.Any) -> typing.Any:
        """
        将 Protobuf 字段值转换为适合 Pydantic 的格式
        
        Args:
            field_name: 字段名
            value: 字段值
            
        Returns:
            Any: 转换后的值
        """
        # 处理列表
        if isinstance(value, list):
            return [cls._convert_field_from_protobuf(field_name, item) for item in value]
        
        # 处理字典
        if isinstance(value, dict):
            return {
                k: cls._convert_field_from_protobuf(f"{field_name}.{k}", v) 
                for k, v in value.items()
            }
        
        # 处理枚举值（Protobuf 中的枚举是整数）
        if isinstance(value, int):
            # 尝试查找对应的枚举类
            enum_class = cls._find_enum_class(field_name)
            if enum_class:
                try:
                    return enum_class(value)
                except ValueError:
                    # 如果枚举值不存在，返回原始值
                    pass
        
        return value
    
    @classmethod
    def _find_enum_class(cls, field_name: str) -> typing.Optional[type]:
        """
        查找字段对应的枚举类
        
        Args:
            field_name: 字段名
            
        Returns:
            Optional[type]: 枚举类，如果找不到则返回 None
        """
        # 获取模型的字段信息
        if hasattr(cls, 'model_fields'):
            field_info = cls.model_fields.get(field_name)
            if field_info:
                field_type = field_info.annotation
                # 检查是否为枚举类型
                if hasattr(field_type, '__bases__'):
                    for base in field_type.__bases__:
                        if base.__name__ == 'IntEnum':
                            return field_type
        return None


# 测试用的枚举
import enum
class TestEnum(enum.IntEnum):
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3


# 测试用的 Pydantic 模型
class TestMessage(ProtobufMixin, BaseModel):
    id: int
    name: str
    value: float
    enum_value: TestEnum
    tags: list[str]


def test_from_protobuf_logic():
    """测试 from_protobuf 的核心逻辑"""
    print("🚀 开始测试 from_protobuf 核心逻辑\n")
    
    # 1. 测试字典预处理
    print("1. 测试字典预处理...")
    test_dict = {
        "id": 123,
        "name": "test_name",
        "value": 45.67,
        "enum_value": 2,  # 对应 TestEnum.VALUE_2
        "tags": ["tag1", "tag2", "tag3"]
    }
    
    processed_dict = TestMessage._prepare_protobuf_dict(test_dict)
    print(f"原始字典：{test_dict}")
    print(f"处理后字典：{processed_dict}")
    
    # 验证枚举转换
    assert processed_dict["enum_value"] == TestEnum.VALUE_2
    print("✅ 字典预处理测试通过\n")
    
    # 2. 测试字段转换
    print("2. 测试字段转换...")
    
    # 测试列表转换
    list_value = ["a", "b", "c"]
    converted_list = TestMessage._convert_field_from_protobuf("tags", list_value)
    assert converted_list == ["a", "b", "c"]
    print("✅ 列表转换测试通过")
    
    # 测试字典转换
    dict_value = {"key1": "value1", "key2": "value2"}
    converted_dict = TestMessage._convert_field_from_protobuf("metadata", dict_value)
    assert converted_dict == {"key1": "value1", "key2": "value2"}
    print("✅ 字典转换测试通过")
    
    # 测试枚举转换
    enum_value = 1
    converted_enum = TestMessage._convert_field_from_protobuf("enum_value", enum_value)
    assert converted_enum == TestEnum.VALUE_1
    print("✅ 枚举转换测试通过")
    
    # 测试无效枚举值
    invalid_enum_value = 999
    converted_invalid = TestMessage._convert_field_from_protobuf("enum_value", invalid_enum_value)
    assert converted_invalid == 999  # 应该返回原始值
    print("✅ 无效枚举值处理测试通过\n")
    
    # 3. 测试完整的模型创建
    print("3. 测试完整的模型创建...")
    try:
        # 模拟从 protobuf 转换来的字典
        pb_dict = {
            "id": 123,
            "name": "test_name",
            "value": 45.67,
            "enum_value": 2,
            "tags": ["tag1", "tag2", "tag3"]
        }
        
        # 预处理字典
        processed_dict = TestMessage._prepare_protobuf_dict(pb_dict)
        
        # 创建模型实例
        instance = TestMessage(**processed_dict)
        
        print(f"创建的模型实例：{instance}")
        
        # 验证结果
        assert instance.id == 123
        assert instance.name == "test_name"
        assert instance.value == 45.67
        assert instance.enum_value == TestEnum.VALUE_2
        assert instance.tags == ["tag1", "tag2", "tag3"]
        
        print("✅ 完整模型创建测试通过\n")
        
    except Exception as e:
        print(f"❌ 模型创建失败：{e}")
        import traceback
        traceback.print_exc()
    
    # 4. 测试错误处理
    print("4. 测试错误处理...")
    
    # 测试缺少必需字段
    try:
        incomplete_dict = {"id": 123}  # 缺少其他必需字段
        TestMessage(**incomplete_dict)
        print("❌ 应该抛出异常但没有")
    except ValidationError as e:
        print(f"✅ 正确捕获缺少字段错误：{e}")
    
    # 测试类型错误
    try:
        wrong_type_dict = {"id": "not_an_int", "name": "test", "value": 1.0, "enum_value": 1, "tags": []}
        TestMessage(**wrong_type_dict)
        print("❌ 应该抛出异常但没有")
    except ValidationError as e:
        print(f"✅ 正确捕获类型错误：{e}")
    
    print("\n🎉 from_protobuf 核心逻辑测试完成！")


if __name__ == "__main__":
    test_from_protobuf_logic() 