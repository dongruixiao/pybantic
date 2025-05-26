# pybantic

## TODO

- [ ] gRPC 的类型系统
  - [x] gRPC 的标量类型
  - [x] gRPC 的枚举类型
  - [x] gRPC 的嵌套类型
  - [ ] gRPC 的 well know 类型
- [ ] gRPC 的特殊字段
  - [ ] gRPC 的 optional 字段，optional 不是 None 而是类型的默认值，且不序列化到 proto 文件中
  - [x] gRPC 的 repeated 字段
  - [x] gRPC 的 map 字段
  - [x] gRPC 的 oneof 字段
  - [ ] gRPC 的 reserved 字段
  - [ ] gRPC 的 extensions 字段
- [ ] Python 的 type annotation 的多种写法
- [ ] pydantic 类型的嵌套
- [ ] 字段编号的问题，如何限制删除编号，reserved 的写法
- [ ] proto 的注释
- [ ] 处理导入的问题，import 的写法
- [ ] 处理 stream 的情况
- [ ] 简化 client 的写法，client 可以继承一个带有 stub 的基类，包装所有 rpc 的方法，并返回一个预定义的 response 的类型，请求需要反序列化成 pydantic 的模型，response 需要序列化成 proto 的定义
- [ ] server 的注册，server 的注册需要考虑多个 server 的情况

```protobuf
/**
 * SearchRequest represents a search query, with pagination options to
 * indicate which results to include in the response.
 */
```
