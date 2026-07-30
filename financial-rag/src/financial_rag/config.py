from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys
    openai_api_key: str
    anthropic_api_key: str
    pinecone_api_key: str

    # Pinecone index config
    pinecone_index_name: str = "financial-rag"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # Embedding config
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Chunking config
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 75


settings = Settings()
