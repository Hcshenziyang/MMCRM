# CRM 项目 Django ORM 详解

本文不是泛泛而谈 Django ORM，而是结合当前 CRM 项目的真实代码结构来讲：

- ORM 在这个项目里是怎么落地的
- 每个模型之间是什么关系
- 平时增删改查应该怎么写
- DRF、权限、缓存、性能优化是如何与 ORM 配合的
- 当前项目里已经体现出来的 ORM 设计经验和注意点

适用代码范围主要是：

- `backend/customer/models.py`
- `backend/project/models.py`
- `backend/aihelper/models.py`
- `backend/customer/views.py`
- `backend/project/views.py`
- `backend/permission/views.py`
- `backend/customer/serializers.py`
- `backend/project/serializers.py`
- `backend/permission/serializers.py`

---

## 1. 什么是 Django ORM

ORM 是 Object Relational Mapping，对象关系映射。

在 Django 里，它的核心作用是：

- 用 Python 类描述数据库表
- 用类的字段描述表字段
- 用对象之间的关系描述外键、多对多等关系
- 用 `QuerySet` 组织查询、过滤、排序、更新、删除

你在代码里看到：

```python
Customer.objects.filter(owner=request.user)
```

本质上等价于“查 customer 表里 owner_id 等于当前用户 id 的记录”，只是 ORM 帮你把 SQL 抽象成了 Python 表达式。

---

## 2. 这个 CRM 项目的 ORM 全景图

这个项目的核心业务实体并不复杂，主要围绕“用户 -> 客户 -> 项目 -> 活动记录”展开。

### 2.1 实体关系图

```text
User
  ├─ 1:N -> Customer.owner
  ├─ 1:N -> Project.owner
  ├─ 1:N -> Activity.created_by
  ├─ 1:N -> AiInteraction.owner
  └─ N:M -> Group -> N:M -> Permission

Customer
  └─ 1:N -> Project.customer

ProjectStage
  └─ 1:N -> Project.current_stage

Project
  └─ 1:N -> Activity.project
```

### 2.2 业务含义

- 一个用户可以拥有多个客户
- 一个客户可以关联多个项目
- 一个项目属于一个阶段
- 一个项目可以有多条跟进活动
- 一个活动由某个用户创建
- AI 交互日志归属于某个用户
- 用户、角色组、权限使用 Django 自带认证模型

这就是 ORM 最擅长的场景：表之间关系很多，但业务代码希望按“对象关系”来写。

---

## 3. 项目中的模型定义怎么理解

## 3.1 Customer：客户模型

文件：`backend/customer/models.py`

核心结构：

```python
class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # TODO，待修改，级联删除业务逻辑不对。
    owner = models.ForeignKey(User, related_name='customers', on_delete=models.CASCADE) 
```

### 字段解释

- `AutoField`：自增主键
- `CharField`：短文本
- `EmailField`：邮箱字段，本质仍存字符串，但会做格式校验
- `DateTimeField(auto_now_add=True)`：创建时自动写入
- `DateTimeField(auto_now=True)`：每次保存时自动更新
- `ForeignKey(User)`：外键到 Django 内置用户表

### 关系解释

`owner = models.ForeignKey(User, related_name='customers', ...)`

表示：

- 正向：`customer.owner` 可以拿到客户所属用户
- 反向：`user.customers.all()` 可以拿到该用户拥有的所有客户

### `on_delete=models.CASCADE`

这表示如果用户被删除，用户拥有的客户也会被级联删除。

这是 ORM 里非常重要的建模决策，因为它直接决定数据生命周期。

---

## 3.2 ProjectStage：项目阶段

文件：`backend/project/models.py`

```python
class ProjectStage(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveSmallIntegerField(unique=True)
    description = models.TextField(blank=True)
```

### 设计含义

- `name` 唯一：同一个阶段名不能重复
- `order` 唯一：阶段顺序不允许冲突
- 这是一个“基础字典表”，通常数据量小、变更频率低

这种表在 ORM 里常见特点是：

- 很少删除
- 经常作为外键被引用
- 适合做筛选、排序、状态流转

---

## 3.3 Project：项目模型

文件：`backend/project/models.py`

```python
class Project(models.Model):
    name = models.CharField(max_length=200)
    customer = models.ForeignKey(Customer, related_name='projects', on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_projects',
                              on_delete=models.SET_NULL, blank=True, null=True)
    current_stage = models.ForeignKey(ProjectStage, related_name='projects_in_stage',
                                      on_delete=models.PROTECT)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='self_generated')
    description = models.TextField(blank=True)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    close_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 这里体现了三种外键删除策略

#### 1. `customer -> CASCADE`

客户删掉时，项目一起删掉。

适合“强依附”关系。

#### 2. `owner -> SET_NULL`

负责人用户删掉时，不删项目，只把 `owner` 置空。

适合“负责人可变，但项目记录要保留”的场景。

#### 3. `current_stage -> PROTECT`

如果还有项目引用某个阶段，就不允许删这个阶段。

适合“字典表/状态表”。

### `choices` 的作用

`source` 字段用了 `choices`：

```python
SOURCE_CHOICES = [
    ('website', '官网咨询'),
    ('phone_call', '电话拜访'),
    ('referral', '客户推荐'),
    ('sales_assignment', '销售主管分配'),
    ('self_generated', '自行开发'),
    ('other', '其他'),
]
```

这意味着：

- 数据库存的是 `'website'`、`'phone_call'`
- 展示层可以拿中文标签
- ORM 中可以用 `project.get_source_display()` 取得展示文本

### 反向关系

- `customer.projects.all()`：某客户下的全部项目
- `stage.projects_in_stage.all()`：某阶段下的全部项目
- `user.owned_projects.all()`：某用户负责的全部项目

---

## 3.4 Activity：项目活动记录

文件：`backend/project/models.py`

```python
class Activity(models.Model):
    project = models.ForeignKey(Project, related_name='activities', on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES, default='call')
    description = models.TextField()
    activity_date = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   related_name='created_activities',
                                   on_delete=models.SET_NULL,
                                   blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-activity_date']
```

### `Meta.ordering`

这是 ORM 默认排序配置。

表示：

- `Activity.objects.all()` 如果没有显式排序
- 默认按 `activity_date` 倒序

这点在列表接口里很常见，因为它能统一默认展示顺序。

### 反向关系

- `project.activities.all()`：某项目下全部活动
- `user.created_activities.all()`：某用户创建的全部活动

---

## 3.5 AiInteraction：AI 交互日志

文件：`backend/aihelper/models.py`

```python
class AiInteraction(models.Model):
    class Intent(models.TextChoices):
        CUSTOMER_CREATE = 'customer.create', '创建客户'
        CUSTOMER_LIST = 'customer.list', '查看客户'
        TALK = 'talk', '闲聊'
        UNKNOWN = 'unknown', '未知意图'
        ERROR = 'error', '处理错误'

    owner = models.ForeignKey(User, related_name='ai_interactions', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    user_input = models.TextField()
    context = models.JSONField(blank=True, null=True)
    intent = models.CharField(max_length=50, choices=Intent.choices, blank=True, null=True)
    slots = models.JSONField(blank=True, null=True)
    generated_command = models.JSONField(blank=True, null=True)
```

### 这里体现的 ORM 点

- `TextChoices`：适合把状态/意图做成强约束枚举
- `JSONField`：适合存结构化但不固定的上下文数据

例如：

```python
AiInteraction.objects.create(
    owner=request.user,
    user_input="帮我创建一个客户",
    context={"page": "customer"},
    intent=AiInteraction.Intent.CUSTOMER_CREATE,
    slots={"name": "张三"},
    generated_command={"action": "create_customer"}
)
```

---

## 3.6 User / Group / Permission：项目没有自定义用户表

这个项目用户、角色组、权限直接使用 Django 自带模型：

- `django.contrib.auth.models.User`
- `django.contrib.auth.models.Group`
- `django.contrib.auth.models.Permission`

这在 `backend/permission/serializers.py` 和 `backend/permission/views.py` 里用得很明显。

说明：

- 本项目并没有自定义 `AUTH_USER_MODEL`
- ORM 里直接操作 Django 内置认证表
- 角色和权限的关系本质是多对多

---

## 4. Django ORM 最核心的对象：QuerySet

在这个项目里，最常出现的就是：

```python
Customer.objects.filter(owner=self.request.user)
Project.objects.filter(owner=self.request.user)
Activity.objects.filter(created_by=self.request.user)
```

这些返回的都不是“立刻查出来的列表”，而是 `QuerySet`。

### QuerySet 有三个关键特点

#### 1. 惰性执行

写下下面代码时，数据库通常还没查：

```python
qs = Customer.objects.filter(owner=request.user)
```

只有在这些时机才会真正发 SQL：

- `list(qs)`
- `for item in qs`
- `qs.count()`
- `qs.exists()`
- 序列化输出
- 模板渲染

#### 2. 可链式拼接

```python
qs = Customer.objects.filter(owner=request.user).order_by('-created_at')
```

#### 3. 不可变风格

每次调用 `filter()`、`exclude()`、`order_by()` 都会返回新 QuerySet，不会改原对象。

---

## 5. 本项目最常见的 ORM 用法

## 5.1 查询当前用户自己的数据

文件：

- `backend/customer/views.py`
- `backend/project/views.py`

示例：

```python
def get_queryset(self):
    return Customer.objects.filter(owner=self.request.user).select_related('owner')
```

这是典型的“数据隔离”写法。

业务含义：

- 不是让用户看到所有客户
- 只返回 `owner = 当前用户` 的记录

同类写法还有：

```python
Project.objects.filter(owner=self.request.user)
Activity.objects.filter(created_by=self.request.user)
```

### 等价 SQL 思路

```sql
SELECT * FROM customer_customer
WHERE owner_id = current_user_id;
```

---

## 5.2 创建对象

### 直接创建

```python
Customer.objects.create(
    name="上海宏达科技",
    phone="13800000000",
    email="sales@example.com",
    address="上海浦东新区",
    owner=request.user
)
```

### 在 DRF `perform_create()` 里创建

项目里常见模式：

```python
def perform_create(self, serializer):
    serializer.save(owner=self.request.user)
```

这本质上仍然是 ORM 的写入，只是通过 serializer 包了一层。

优点：

- 前端不需要传 `owner`
- 后端统一接管归属关系
- 避免恶意伪造他人 owner

---

## 5.3 根据主键查询单条记录

项目导入 Excel 时用了：

```python
customer = Customer.objects.get(id=customer_id)
```

特点：

- 查到 1 条返回对象
- 查不到抛 `Customer.DoesNotExist`
- 查到多条抛 `MultipleObjectsReturned`

所以实际业务里通常会配合异常处理：

```python
try:
    customer = Customer.objects.get(id=customer_id, owner=request.user)
except Customer.DoesNotExist:
    ...
```

### `get()` 和 `filter().first()` 的区别

#### `get()`

- 强约束：预期只能有 1 条
- 出错就抛异常

#### `first()`

- 更宽松
- 没有返回 `None`

例如：

```python
customer = Customer.objects.filter(id=customer_id, owner=request.user).first()
if not customer:
    ...
```

---

## 5.4 更新对象

项目导入 Excel 时用了最典型的实例更新：

```python
customer.name = name
customer.phone = phone
customer.email = email
customer.address = address
customer.save()
```

这是“先查出对象，再修改，再保存”。

适合：

- 需要业务校验
- 需要触发模型方法/信号
- 需要改多个字段

### 批量更新写法

如果不需要逐条实例逻辑，也可以：

```python
Customer.objects.filter(owner=request.user, id=customer_id).update(
    name="新名称",
    updated_at=timezone.now(),
)
```

区别：

- `update()` 直接发 SQL
- 不会调用实例的 `save()`
- 不会走模型层自定义保存逻辑

---

## 5.5 删除对象

### 删除单个对象

```python
customer = Customer.objects.get(id=1, owner=request.user)
customer.delete()
```

### 按条件删除

```python
Customer.objects.filter(owner=request.user, created_at__lt=some_time).delete()
```

但在 CRM 这类业务里，删除通常要谨慎，因为外键删除策略会联动：

- 删除 `Customer` 会级联删除 `Project`
- 删除 `Project` 会级联删除 `Activity`

所以 ORM 删除不是只删一张表，而可能触发整条业务链上的数据清理。

---

## 6. 外键关系怎么用

## 6.1 正向访问

正向访问就是“我有当前对象，要拿它关联的对象”。

### 例子

```python
project = Project.objects.get(id=10)
customer = project.customer
owner = project.owner
stage = project.current_stage
```

`project.customer` 背后就是通过外键去找 `Customer`。

---

## 6.2 反向访问

反向访问就是“我有被引用对象，要拿所有引用它的对象”。

这个能力来自 `related_name`。

### 例子

```python
user.customers.all()
customer.projects.all()
project.activities.all()
stage.projects_in_stage.all()
user.created_activities.all()
user.ai_interactions.all()
```

如果没有写 `related_name`，Django 会自动生成默认名，例如 `xxx_set`。  
当前项目大部分地方都主动写了 `related_name`，这是正确的，能让代码更可读。

---

## 6.3 跨表过滤

Django ORM 支持双下划线跨关系查询。

### 例子

查“当前用户名下，且阶段名为成交的项目”：

```python
Project.objects.filter(
    owner=request.user,
    current_stage__name='成交'
)
```

查“某个客户下，来源为官网咨询的项目”：

```python
Project.objects.filter(
    customer__id=customer_id,
    source='website'
)
```

查“项目名包含 AI，且客户名包含 上海 的活动记录”：

```python
Activity.objects.filter(
    project__name__icontains='AI',
    project__customer__name__icontains='上海'
)
```

### 项目中的一个典型注意点

`backend/project/views.py` 里有：

```python
search_fields = ['name', 'customer_name']
```

如果希望按关联客户名搜索，ORM 的标准写法应是：

```python
search_fields = ['name', 'customer__name']
```

这里正好能看出 Django ORM 跨表字段命名的规则：`关联字段__目标字段`。

---

## 7. `select_related` 和 `prefetch_related`

这是 Django ORM 性能优化最重要的一组 API。

---

## 7.1 `select_related`：适合外键、一对一

项目里大量使用了：

```python
Customer.objects.filter(owner=self.request.user).select_related('owner')
Project.objects.all().select_related("customer", "owner", "current_stage")
Activity.objects.all().select_related("project", "created_by")
```

### 为什么需要它

如果你先查项目列表，再循环里访问：

```python
for project in projects:
    print(project.customer.name)
```

不做优化时，可能出现：

- 1 次查项目
- N 次查 customer

也就是 N+1 查询问题。

`select_related()` 会通过 SQL JOIN 一次把外键对象查出来。

### 适用关系

- `ForeignKey`
- `OneToOneField`

### 不适合

- `ManyToManyField`
- 反向一对多

---

## 7.2 `prefetch_related`：适合多对多、反向关系

项目里权限模块用了：

```python
User.objects.all().prefetch_related('groups')
```

以及：

```python
Group.objects.prefetch_related(
    'permissions',
    Prefetch('user_set', queryset=User.objects.prefetch_related('groups'))
)
```

### 为什么这里要用 `prefetch_related`

因为：

- `User <-> Group` 是多对多
- `Group <-> Permission` 是多对多

这类关系不适合 `select_related()`，因为不是一条 JOIN 就能优雅解决的。

`prefetch_related()` 的策略是：

- 先查主表
- 再查关联表
- 在 Python 内存中做映射拼装

### 适用关系

- `ManyToManyField`
- 反向 `ForeignKey`
- 需要自定义预取条件时

---

## 7.3 当前项目里一个很值得注意的细节

在 `backend/project/views.py` 里，类属性写了：

```python
queryset = Project.objects.all().select_related("customer", "owner", "current_stage")
```

但后面又重写了：

```python
def get_queryset(self):
    return Project.objects.filter(owner=self.request.user).select_related('owner')
```

这意味着真正生效的是 `get_queryset()` 返回值。  
也就是说，最终实际只 `select_related('owner')`，没有把 `customer` 和 `current_stage` 一起优化进去。

这就是 ORM 使用里常见的一个点：

- 类属性 `queryset`
- 方法 `get_queryset()`

如果同时存在，通常要以 `get_queryset()` 为准。

同样的问题在 `ActivityViewSet` 里也有类似表现。

---

## 8. 序列化器是如何驱动 ORM 关系写入的

## 8.1 CustomerSerializer

文件：`backend/customer/serializers.py`

```python
class CustomerSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
```

这意味着：

- 读取时返回 owner 的字符串表示
- 写入时前端不允许直接改 owner
- owner 由视图层 `perform_create()` 决定

这是很标准的 ORM + DRF 协作方式。

---

## 8.2 ProjectSerializer：读写分离

文件：`backend/project/serializers.py`

```python
customer = CustomerSimpleSerializer(read_only=True)
owner = UserSimpleSerializer(read_only=True)
current_stage = ProjectStageSerializer(read_only=True)

customer_id = serializers.PrimaryKeyRelatedField(
    queryset=Customer.objects.all(),
    source='customer'
)
current_stage_id = serializers.PrimaryKeyRelatedField(
    queryset=ProjectStage.objects.all(),
    source='current_stage'
)
```

### 这段设计非常值得学

它把“显示对象”和“写入关系”分开了：

- 读的时候，返回嵌套对象
- 写的时候，只收外键 id

前端创建项目时可以传：

```json
{
  "name": "华东大区数字化改造",
  "customer_id": 3,
  "current_stage_id": 2,
  "source": "website"
}
```

ORM 会把它转换成：

- `project.customer = Customer(id=3)`
- `project.current_stage = ProjectStage(id=2)`

这是 Django REST Framework 和 ORM 配合的常见模式。

---

## 8.3 Group/User 权限模块中的多对多写入

文件：`backend/permission/serializers.py`

例如用户序列化器：

```python
groups_write = serializers.PrimaryKeyRelatedField(
    many=True,
    queryset=Group.objects.all(),
    write_only=True,
    required=False
)
```

创建用户时：

```python
user = User.objects.create(**validated_data)
user.groups.set(groups_data)
user.save()
```

这里的关键 ORM API 是：

```python
user.groups.set(groups_data)
```

对于多对多字段，常见写法有：

- `set([...])`：整体替换
- `add(obj1, obj2)`：追加
- `remove(obj)`：移除
- `clear()`：清空

例子：

```python
user.groups.add(group1, group2)
user.groups.remove(group1)
user.groups.clear()
```

---

## 9. 项目中的权限缓存，本质上也和 ORM 有关

文件：`backend/mycrm/permissions.py`

这里做了两件事：

### 1. 用 ORM 读取用户权限

```python
perms = list(user.get_all_permissions())
```

虽然这是 Django auth 封装好的方法，但底层仍依赖 ORM 去查：

- 用户直接权限
- 用户所属组权限

### 2. 用信号监听多对多变化

```python
@receiver(m2m_changed, sender=User.groups.through)
def user_groups_changed(sender, instance, **kwargs):
    clear_user_perm_cache(instance)
```

这里体现了 ORM 的另一个重要部分：信号。

当这些关系变化时：

- `User.user_permissions`
- `User.groups`
- `Group.permissions`

对应缓存会清理，避免权限数据过期。

---

## 10. 结合本项目的常见 ORM 操作示例

## 10.1 客户模块

### 查询我的全部客户

```python
customers = Customer.objects.filter(owner=request.user).order_by('-created_at')
```

### 搜索客户

```python
customers = Customer.objects.filter(
    owner=request.user,
    name__icontains='科技'
)
```

### 判断客户是否存在

```python
exists = Customer.objects.filter(
    owner=request.user,
    email='sales@example.com'
).exists()
```

### 统计我的客户数

```python
count = Customer.objects.filter(owner=request.user).count()
```

---

## 10.2 项目模块

### 查询某客户的项目

```python
projects = Project.objects.filter(customer_id=customer_id)
```

### 查询当前用户负责且未成交的项目

```python
projects = Project.objects.filter(
    owner=request.user
).exclude(
    current_stage__name='成交'
)
```

### 查询某阶段下项目

```python
projects = Project.objects.filter(current_stage__order=2)
```

### 创建项目

```python
project = Project.objects.create(
    name='ERP 升级项目',
    customer=customer,
    owner=request.user,
    current_stage=stage,
    source='referral',
    revenue=500000.00
)
```

---

## 10.3 活动记录模块

### 查询某项目下的活动

```python
activities = Activity.objects.filter(project=project).select_related('created_by')
```

### 查询当前用户本月创建的活动

```python
activities = Activity.objects.filter(
    created_by=request.user,
    activity_date__month=timezone.now().month
)
```

### 创建活动

```python
Activity.objects.create(
    project=project,
    activity_type='meeting',
    description='与客户进行方案评审',
    activity_date=timezone.now(),
    created_by=request.user,
)
```

---

## 10.4 AI 日志模块

### 查询最近 20 条 AI 交互

```python
logs = AiInteraction.objects.filter(owner=request.user)[:20]
```

### 查询“创建客户”意图的日志

```python
logs = AiInteraction.objects.filter(
    intent=AiInteraction.Intent.CUSTOMER_CREATE
)
```

### 根据 JSON 内容做过滤

如果数据库版本和 Django 版本支持，也可以做：

```python
logs = AiInteraction.objects.filter(context__page='customer')
```

---

## 11. ORM 里的聚合、统计、注解

当前项目代码里没有大规模使用 `annotate()` / `aggregate()`，但 CRM 场景非常适合这类查询。

需要先导入：

```python
from django.db.models import Count, Sum
```

### 统计每个客户的项目数

```python
customers = Customer.objects.filter(owner=request.user).annotate(
    project_count=Count('projects')
)

for customer in customers:
    print(customer.name, customer.project_count)
```

### 统计每个阶段的项目数

```python
stages = ProjectStage.objects.annotate(
    project_count=Count('projects_in_stage')
)
```

### 统计当前用户负责项目的总金额

```python
result = Project.objects.filter(owner=request.user).aggregate(
    total_revenue=Sum('revenue')
)
```

返回结果类似：

```python
{'total_revenue': Decimal('880000.00')}
```

这类能力在 CRM 看板、销售漏斗、业绩统计里非常常用。

---

## 12. 事务：当前项目适合补上的 ORM 能力

当前项目没有显式使用 `transaction.atomic()`，但有些场景非常适合加事务。

例如 `backend/customer/views.py` 的 Excel 导入：

- 一次循环创建/更新很多客户
- 中间某条失败，前面可能已经写入数据库

如果希望“要么全成功，要么全回滚”，就应该使用事务。

示例：

```python
from django.db import transaction

with transaction.atomic():
    for row in rows:
        Customer.objects.create(...)
```

### 什么时候要事务

- 一次请求里要写多张表
- 批量导入
- 先创建主记录，再创建子记录
- 涉及库存、金额、状态流转一致性

### 什么时候不一定要

- 单条简单查询
- 单条简单更新

---

## 13. ORM 性能优化建议

结合本项目，重点是这几类。

## 13.1 列表页优先考虑 N+1 查询

例如项目列表如果要展示：

- 项目名
- 客户名
- 负责人
- 当前阶段

就应该：

```python
Project.objects.select_related('customer', 'owner', 'current_stage')
```

而不是查出项目后再逐个访问关联对象。

---

## 13.2 多对多列表优先考虑预取

权限管理里：

- 用户列表带组
- 组列表带权限、用户

就应使用 `prefetch_related()`。

这点项目里已经做了正确示范。

---

## 13.3 只查需要的字段

如果只是导出某些字段，理论上也可以：

```python
Customer.objects.filter(owner=request.user).values(
    'id', 'name', 'phone', 'email'
)
```

或者：

```python
Customer.objects.only('id', 'name', 'phone', 'email')
```

适合：

- 只做轻量列表返回
- 导出
- 后台统计

---

## 13.4 用 `exists()` 判断存在性，不要先查全量

推荐：

```python
Customer.objects.filter(email=email, owner=request.user).exists()
```

不推荐：

```python
len(Customer.objects.filter(email=email, owner=request.user)) > 0
```

前者更直接，也更节省资源。

---

## 13.5 批量写入可以考虑 `bulk_create`

如果 Excel 导入是“纯新增”，可以考虑：

```python
Customer.objects.bulk_create(customer_list, batch_size=500)
```

优点：

- SQL 次数少
- 导入速度快

注意：

- 不会逐条调用 `save()`
- 某些信号不会按普通保存方式触发

---

## 14. Django ORM 常见双下划线查询语法

这个项目做搜索、过滤时会频繁用到。

### 常见比较

```python
Customer.objects.filter(name__icontains='科技')
Customer.objects.filter(created_at__date='2026-03-25')
Project.objects.filter(revenue__gte=100000)
Project.objects.filter(close_date__isnull=False)
Activity.objects.filter(activity_date__year=2026)
```

### 跨表

```python
Project.objects.filter(customer__name__icontains='上海')
Activity.objects.filter(project__customer__owner=request.user)
```

### 范围

```python
Project.objects.filter(created_at__range=[start_time, end_time])
```

---

## 15. 与 DRF 配合时，ORM 在请求链路中的位置

以创建项目为例，完整链路通常是：

### 1. 请求进入 ViewSet

`backend/project/views.py`

### 2. Serializer 校验参数

`backend/project/serializers.py`

- `customer_id` 校验对应客户是否存在
- `current_stage_id` 校验对应阶段是否存在

### 3. `serializer.save(owner=request.user)`

这里才真正调用 ORM 写库。

### 4. 读取返回结果时，再次通过 ORM 关系取值

- 返回嵌套 `customer`
- 返回嵌套 `owner`
- 返回嵌套 `current_stage`

所以在 Django REST Framework 项目里，ORM 几乎贯穿请求全流程。

---

## 16. 当前 CRM 项目里值得掌握的 ORM 设计经验

## 16.1 `related_name` 要主动命名

当前项目这一点做得比较好：

- `customers`
- `projects`
- `owned_projects`
- `projects_in_stage`
- `activities`
- `created_activities`
- `ai_interactions`

优点：

- 可读性高
- 反向关系表达清晰

---

## 16.2 归属字段应该由后端接管

项目里 `owner`、`created_by` 基本都由后端 `perform_create()` 写入。

这是正确做法。

原因：

- 权限边界明确
- 防止越权
- 前端表单更简单

---

## 16.3 基础字典表适合 `PROTECT`

项目阶段 `ProjectStage` 是典型字典表。

把它的删除策略设为 `PROTECT` 很合理，因为：

- 阶段记录不应轻易删除
- 历史项目要保留语义完整性

---

## 16.4 审计型数据适合 `SET_NULL` 或保留主记录

如：

- 项目负责人 `owner`
- 活动创建人 `created_by`

即使用户被删除，业务记录仍要保留。这种地方用 `SET_NULL` 比 `CASCADE` 更稳妥。

---

## 17. 学 Django ORM 时，建议按这个项目来建立认知

如果你把这个 CRM 项目当作练习样板，建议按以下顺序掌握：

### 第一阶段：模型层

- 看懂 `Customer`
- 看懂 `Project`
- 看懂 `Activity`
- 理解 `ForeignKey`、`related_name`、`on_delete`

### 第二阶段：查询层

- `filter()`
- `get()`
- `exclude()`
- `order_by()`
- `exists()`
- `count()`

### 第三阶段：跨表查询

- `customer__name`
- `project__customer__owner`
- `current_stage__name`

### 第四阶段：性能层

- `select_related()`
- `prefetch_related()`
- `annotate()`
- `aggregate()`

### 第五阶段：工程化层

- serializer 驱动关系写入
- `perform_create()` 注入归属人
- 权限和 ORM 联动
- 事务和批量导入

---

## 18. 一组结合本项目的完整示例

## 18.1 创建客户 -> 创建项目 -> 创建活动

```python
from django.contrib.auth.models import User
from customer.models import Customer
from project.models import Project, ProjectStage, Activity
from django.utils import timezone

user = User.objects.get(username='alice')

customer = Customer.objects.create(
    name='杭州云启信息',
    email='biz@yq.com',
    phone='13900000000',
    address='杭州滨江区',
    owner=user,
)

stage = ProjectStage.objects.get(name='销售')

project = Project.objects.create(
    name='CRM 系统采购',
    customer=customer,
    owner=user,
    current_stage=stage,
    source='website',
    description='客户来自官网咨询',
    revenue=120000.00,
)

Activity.objects.create(
    project=project,
    activity_type='meeting',
    description='首次需求沟通会议',
    activity_date=timezone.now(),
    created_by=user,
)
```

## 18.2 查询项目并带出客户、阶段、活动

```python
projects = Project.objects.filter(
    owner=user
).select_related(
    'customer', 'owner', 'current_stage'
).prefetch_related(
    'activities'
)

for project in projects:
    print(project.name, project.customer.name, project.current_stage.name)
    for act in project.activities.all():
        print(' - ', act.activity_type, act.activity_date)
```

这个例子把 Django ORM 三件事串起来了：

- 主查询：`filter`
- 外键优化：`select_related`
- 反向一对多优化：`prefetch_related`

---

## 19. 总结

对于这个 CRM 项目，Django ORM 的主线可以概括成一句话：

> 用模型表达业务实体，用外键表达业务关系，用 QuerySet 表达业务查询，用 serializer 和 ViewSet 把 ORM 接进接口层。

如果从项目实战角度看，最关键的是掌握这几件事：

- 看懂模型之间的关系
- 熟练写 `filter/get/create/save/delete`
- 会写跨表查询
- 会用 `select_related` / `prefetch_related`
- 明白 `serializer.save()` 背后仍是 ORM 写库
- 知道什么时候需要事务和批量操作

如果后续你要继续扩展这个 CRM，比如做：

- 销售漏斗统计
- 客户标签
- 跟进提醒
- 审批流
- AI 指令落库与回放

本质上都还是在 Django ORM 这套能力上继续往前长。
