from datetime import datetime
from fastapi import Request
from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String,BigInteger,DateTime,UnicodeText,Float,JSON, func, inspect
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import select

from .database import Base

class Chat(Base):
    __tablename__ = "Chats"

    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    StartDate = Column(DateTime,index=True)
    EndDate = Column(DateTime)
    CustomerId = Column(String(255),index=True)
    CustomerName = Column(UnicodeText)
    Role = Column(UnicodeText)
    Platform = Column(String(255))
    DocumentAttached = Column(UnicodeText)
    Type = Column(String(50))
    ClientMappingId = Column(BigInteger,ForeignKey("ClientRegionMapping.Id"),index=True)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())  
    DocumentAnalysis = Column(UnicodeText)                                               

    # Completions = relationship("Completion", back_populates="Chat")
    Conversation = relationship("Conversation", back_populates="Chat")
    # ErrorCompletions = relationship("ErrorCompletions", back_populates="Chat")
    ClientRegionMapping = relationship("ClientRegionMapping", back_populates="Chat")    

    Index("idx_chat_customer_platform", CustomerId,Platform)

    @hybrid_property
    def region(self):
        return self.ClientRegionMapping.Region if self.ClientRegionMapping else "Unknown"

    @region.expression
    def region(cls):
        return select(ClientRegionMapping.Region).where(ClientRegionMapping.Id == cls.ClientMappingId).scalar_subquery()


class ChatStatus(Base):
    __tablename__ = "ChatStatus"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)  
    ChatId = Column(BigInteger)  
    SessionId = Column(String(255))
    ConversationId = Column(BigInteger)  
    DisplayStatus = Column(String(255))         

class CompletionCategory(Base):
    __tablename__ = "CompletionCategory"
    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    Category = Column(String(255),index=True) # Entity or Help Bot 
    Conversation = relationship("Conversation", back_populates="CompletionCategory")
    IsChargeable = Column(Boolean, default= False)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now()) 

class PromptType(Base):
    __tablename__ = "PromptType"
    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    Type = Column(String) #  LLM0 or LLM2 OR entity_search
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now()) 

class Conversation(Base):
    __tablename__ = "Conversations"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    UserPrompt = Column(UnicodeText)
    IsError = Column(Boolean, default=False)
    ChatId = Column(BigInteger, ForeignKey("Chats.Id"),index=True)
    StatusId = Column(Integer, ForeignKey("CompletionStatuses.Id"),index=True)
    CategoryId = Column(BigInteger, ForeignKey("CompletionCategory.Id"),index=True)
    CreatedAt = Column(DateTime, server_default=func.now(),index=True)
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())                                                     
    FromCache = Column(Boolean, default=False)


    Chat = relationship("Chat", back_populates="Conversation")
    CompletionStatus = relationship("CompletionStatus", back_populates="Conversation")
    CompletionCategory = relationship("CompletionCategory", back_populates="Conversation")
    ConversationPrompt = relationship("ConversationPrompt", back_populates="Conversation")
    ConversationError = relationship("ConversationError", back_populates="Conversation")
    Feedback = relationship("Feedback", back_populates="Conversation")
    Analytics = relationship("Analytics", back_populates="Conversation")

    Index("idx_conversation_chat_created", ChatId, CreatedAt)






class ConversationPrompt(Base):
    __tablename__ = "ConversationPrompts"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    ConversationId = Column(BigInteger, ForeignKey("Conversations.Id"),index=True)
    PromptId = Column(BigInteger, ForeignKey("PromptConfigurationsVersion.Id"),index=True)
    PromptVersion = Column(BigInteger)
    RequestPromptParameters = Column(JSON)
    Response = Column(UnicodeText)
    FromCache= Column(Boolean)
    PromptTokens = Column(BigInteger)
    CompletionTokens = Column(BigInteger)
    StartTime = Column(DateTime)
    EndTime = Column(DateTime)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    Conversation = relationship("Conversation", back_populates="ConversationPrompt")
    PromptConfigurationVersion = relationship("PromptConfigurationsVersion", back_populates="ConversationPrompt")
    Index("idx_prompt_conversation_time", ConversationId, StartTime)

class ConversationError(Base):
    __tablename__ = "ConversationErrors"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    ConversationId = Column(BigInteger, ForeignKey("Conversations.Id"))
    Error = Column(UnicodeText)
    ErrorDetails = Column(UnicodeText)
    ErrorCode = Column(Integer)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    Conversation = relationship("Conversation", back_populates="ConversationError")


class Feedback(Base):
    __tablename__ = "Feedbacks"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    ConversationId = Column(BigInteger, ForeignKey("Conversations.Id"))
    UserSatisfaction = Column(Integer)
    UserNote = Column(String)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    Conversation = relationship("Conversation", back_populates="Feedback")

class Analytics(Base):
    __tablename__ = "Analytics"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    ConversationId = Column(BigInteger, ForeignKey("Conversations.Id"))
    TotalPromptTokens = Column(BigInteger)
    TotalCompletionTokens = Column(BigInteger)
    PromptTokensCost = Column(Float)
    CompletionTokensCost = Column(Float)
    ResponseStartTime = Column(DateTime)
    ResponseEndTime = Column(DateTime)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    Conversation = relationship("Conversation", back_populates="Analytics")

class Question(Base):
    __tablename__ = "Questions"

    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    Question = Column(UnicodeText)   #DataType UnicodeText represents NVARCHAR(max) in SQL
    Title = Column(UnicodeText)
    Context = Column(UnicodeText)
    Platform = Column(UnicodeText)
    UserRole = Column(UnicodeText)
    RankOrder = Column(Integer)
    Active = Column(Boolean)
    Type = Column(String(255))
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Completions = relationship("Completion",back_populates="Question")
    async def __admin_repr__(self, request: Request):
        return f"{self.Question}"

class CompletionStatus(Base):
    __tablename__ = "CompletionStatuses"

    Id = Column(Integer, primary_key=True,autoincrement=True)
    Value = Column(String(50))
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Completions = relationship("Completion",back_populates="CompletionStatus")
    Conversation = relationship("Conversation",back_populates="CompletionStatus")
    # ErrorCompletions = relationship("ErrorCompletions", back_populates="CompletionStatus")
    GroupCompletions = relationship("GroupCompletions", back_populates="CompletionStatus")

    async def __admin_repr__(self, request: Request):
        return f"{self.Value}"


class UserRole(Base):
    __tablename__ = "UsersRole"
    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    RoleName = Column(String(50), unique=True, nullable=False)
    AccessibleScreens = Column(String(500))  # Storing as a comma-separated string
    AccessibleModels = Column(String(500))  # Storing as a comma-separated string
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "Users"
    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    Name = Column(String(50))
    userName = Column(String(100),unique=True,index=True)
    password = Column(String(300))
    IsAdmin = Column(Boolean, default=False)
    RoleId = Column(BigInteger, ForeignKey('UsersRole.Id'),index=True)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    role = relationship("UserRole", back_populates="users")
    PromptConfigurationsHistory = relationship("PromptConfigurationsHistory", back_populates="User")
    AssignedGroupCompletions = relationship("GroupCompletions", back_populates="AssigneeUser")


class SystemMessagePrompt(Base):
    __tablename__ = "SystemMessagePrompts"

    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    name = Column(String(50),unique=True)
    systemPrompt = Column(UnicodeText)
    chatParameters = Column(UnicodeText)
    result = Column(UnicodeText)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

class InputFilesRefreshLog(Base):
    __tablename__ = "InputFilesRefreshLog"
    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    FileId = Column(String(50))
    ParentID = Column(String(50))
    Title = Column(String(200))
    URL = Column(UnicodeText)
    Status = Column(String(50))
    Reason = Column(String(200))
    UploadedToBlobStatus = Column(String(50))
    Persona = Column(String(50))
    Keywords = Column(String(200))
    ContainerName = Column(String(50))
    LastModifiedDate = Column(DateTime)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self,data):
        self.FileId= data['FileId']
        self.ParentID= data['ParentID']
        self.Title= data['Title']
        self.URL= data['URL']
        self.Status= data['Status']
        self.Reason= data['Reason']
        self.UploadedToBlobStatus= data['UploadedToBlobStatus']
        self.Persona= data['Persona']
        self.Keywords= data['Keywords']
        self.ContainerName = data['ContainerName']
        self.LastModifiedDate= data['LastModifiedDate']

class NavigationLinks(Base):
    __tablename__ = "NavigationLinks"
    
    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    name = Column(String(50),index=True)
    responseText = Column(UnicodeText)
    url = Column(UnicodeText)
    type = Column(String(50))
    EntityTypeSupported = Column(String(100), nullable=True)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
    Description = Column(String(255))
    IsActive = Column(Boolean, default=True)
    RequiredId = Column(String(100))
    
class NavigationLinksGlobalConfiguration(Base):
    __tablename__ = "NavigationLinksGlobalConfiguration"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    data = Column(UnicodeText, nullable=True)  
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())      

# class PromptConfiguration(Base):
#     __tablename__ = "PromptConfigurations"

#     Id = Column(BigInteger, primary_key=True,autoincrement=True)
#     name = Column(String(50),unique=True)
#     systemPrompt = Column(UnicodeText)
#     chatParameters = Column(UnicodeText)
#     isReadingCache = Column(Boolean, default=False)
#     isWritingCache = Column(Boolean, default=False)
#     model = Column(String(50))
#     configurations = Column(JSON)
#     RoleAccess = Column(JSON)
#     CreatedAt = Column(DateTime, server_default=func.now())
#     UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

#     ConversationPrompt = relationship("ConversationPrompt", back_populates="PromptConfiguration")

#     def to_dict(self):
#         return {column.key: getattr(self, column.key) for column in inspect(self).mapper.column_attrs}


class AuditLog(Base):
    __tablename__ = 'AuditLog'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    ModuleName = Column(String)
    Action = Column(UnicodeText, nullable=False)
    Description = Column(String, nullable=False)
    Metadata = Column(JSON, nullable=True)
    Timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    UserId = Column(Integer, nullable=True)
    UserName = Column(UnicodeText, nullable=False)
    isError = Column(Boolean)
    ErrorDetails = Column(UnicodeText, nullable=False)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
        
class ScreenConfiguration(Base):
    __tablename__ = "ScreenConfigurations"

    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    primarySchema = Column(String(50),index=True)
    alias = Column(String(50),index=True)
    entityType = Column(String(50))
    metaFieldNames = Column(JSON)
    nestedScreenSpec = Column(JSON)
    promptSpec = Column(UnicodeText)
    screenSelectionSpec = Column(UnicodeText)
    DefaultSchemaId = Column(Integer, ForeignKey("ScreenDefaultSchemas.Id"),index=True)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
    SuggestionActions = Column(JSON)
    screenDescription = Column(String)
    
    DefaultSchema = relationship("ScreenDefaultSchemas", back_populates="ScreenConfigurations")
    PrimarySchemaMapping = relationship("PrimarySchemaMapping", back_populates="ScreenConfigurations")
    async def __admin_repr__(self, request: Request):
        return f"{self.primarySchema}"

class ScreenDefaultSchemas(Base):
    __tablename__ = "ScreenDefaultSchemas"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    screenName =  Column(String(50), unique=True, nullable=False)
    defaultNestedJsonSchema = Column(UnicodeText)
    newDefaultJsonSchema = Column(UnicodeText)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship with ScreenConfigurations
    ScreenConfigurations = relationship("ScreenConfiguration", back_populates="DefaultSchema")
    async def __admin_repr__(self, request: Request):
        return f"{self.Id}"
    
class PrimarySchemaMapping(Base):
    __tablename__ = "PrimarySchemaMapping"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    ClientDetailsId = Column(BigInteger, ForeignKey("ClientRegionMapping.Id"))
    PrimarySchemaId = Column(BigInteger, ForeignKey("ScreenConfigurations.Id"), nullable=False)
    JsonSchema = Column(UnicodeText, nullable=True)  # Assuming this column stores JSON data
    NestedJsonSchema = Column(UnicodeText)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    ScreenConfigurations = relationship("ScreenConfiguration", back_populates="PrimarySchemaMapping")
    client_region_mapping = relationship("ClientRegionMapping", back_populates="primary_schema_mappings")
    Index("idx_client_schema",ClientDetailsId,PrimarySchemaId)

    
class ClientRegionMapping(Base):
    __tablename__ = "ClientRegionMapping"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    ClientId = Column(String(255), nullable=False,index=True)
    ClientName = Column(UnicodeText, nullable=True)
    Region = Column(String(255), nullable=False,index=True)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Define relationship to PrimarySchemaMapping if needed
    primary_schema_mappings = relationship("PrimarySchemaMapping", back_populates="client_region_mapping")

    # Relationships to Chat
    Chat = relationship("Chat", back_populates="ClientRegionMapping")
    Index("idx_client_region", ClientId, Region)


    # Define admin representation
    async def __admin_repr__(self, request: Request):
        return f"ClientId: {self.ClientId}, Region: {self.Region}"
    
class TokenPrice(Base):
    __tablename__ = "TokenPrices"

    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    Model = Column(String(100))
    DeploymentName = Column(String(100))
    Type = Column(String(100))
    Currency = Column(UnicodeText)
    Region = Column(String(100))
    InputTokensPrice = Column(Float)
    OutputTokensPrice = Column(Float)
    Status = Column(Boolean, default=False)
    StartDate = Column(DateTime)
    EndDate = Column(DateTime)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

class GroupCompletions(Base):
    __tablename__ = "GroupCompletions"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    UserPrompt = Column(String)
    Notes = Column(UnicodeText)
    StatusId = Column(Integer, ForeignKey('CompletionStatuses.Id'))
    Category = Column(UnicodeText)
    Assignee = Column(BigInteger, ForeignKey('Users.Id'))
    Count = Column(Integer, default=0)
    AverageScore = Column(Float)
    LastCompletionScore = Column(Float)
    LastCompletionTime = Column(DateTime)
    Role = Column(String(255))
    Platform = Column(String(255))
    LastCompletionId = Column(BigInteger)
    Client = Column(String(255))
    Region = Column(String(255))
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    CompletionStatus = relationship("CompletionStatus",back_populates="GroupCompletions")
    AssigneeUser = relationship("User", back_populates="AssignedGroupCompletions")
    Index("idx_group_completions_query", 
      Role, 
      Platform, 
      Client, 
      Region)

class GlobalConfigurations(Base):
    __tablename__ = "GlobalConfigurations"

    Id = Column(BigInteger, primary_key=True,autoincrement=True)
    name = Column(UnicodeText)
    data = Column(UnicodeText)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

class GEMSUserRole(Base):
    __tablename__ = "GEMSUserRole"
    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    RoleName = Column(String(50), unique=True, nullable=False)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PromptConfigurationsHistory(Base):
    __tablename__ = "PromptConfigurationsHistory"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    systemPrompt = Column(UnicodeText)
    chatParameters = Column(UnicodeText)
    isReadingCache = Column(Boolean, default=False)
    isWritingCache = Column(Boolean, default=False)
    model = Column(String(50))
    configurations = Column(JSON)
    RoleAccess = Column(JSON)
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
    VersionNumber = Column(BigInteger)
    UserId = Column(BigInteger, ForeignKey("Users.Id"), nullable=False)

    User = relationship("User", back_populates="PromptConfigurationsHistory")
    PromptVersions = relationship("PromptConfigurationsVersion", back_populates="Version")

class PromptConfigurationsVersion(Base):
    __tablename__ = "PromptConfigurationsVersion"

    Id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True)
    PromptHistoryId = Column(BigInteger, ForeignKey("PromptConfigurationsHistory.Id"), nullable=False)

    Version = relationship("PromptConfigurationsHistory", back_populates="PromptVersions")
    ConversationPrompt = relationship("ConversationPrompt", back_populates="PromptConfigurationVersion")
