from typing import List
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
import ollama

# PERSIST_DIRECTORY = "./chroma_db"
DB_PATH = './dataBase'
embedding_model = SentenceTransformer("shibing624/text2vec-base-chinese")
chromadb_client = chromadb.PersistentClient()
chromadb_collection = chromadb_client.get_or_create_collection(name="default")

def split_into_chunks(doc_file:str) -> List[str]:
    """
    将指定的知识文本按行分片
    """
    with open(doc_file, 'r', encoding='utf-8') as file:
        content = file.read()
    return [chunk for chunk in content.split("\n\n")]

def embed_chunk(chunk:str) -> List[float]:
    """
    将文本串转换为向量嵌入形式
    """
    embedding = embedding_model.encode(chunk, normalize_embeddings=True)
    return embedding.tolist()

def save_embeddings(chunks:List[str], embeddings: List[List[float]]) -> None:
    """
    将文本块和对应的向量嵌入到ChromaDB中
    """
    for i,(chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chromadb_collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[str(i)]
        )

def retrieve(query: str, top_k: int) -> List[str]:
    """
    寻找和query最相似的top_k个文本块
    """
    query_embedding = embed_chunk(query)
    results = chromadb_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results['documents'][0]

def rerank(query: str, retrieved_chunks: List[str], top_k: int) -> List[str]:
    """
    利用交叉编码器对检索到的文本块进行重排
    """
    cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
    pairs = [(query, chunk) for chunk in retrieved_chunks]
    scores = cross_encoder.predict(pairs)
    scored_chunks = list(zip(retrieved_chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in scored_chunks][:top_k]

def generate(query: str, chunks: List[str]) -> str:
    """根据用户查询和相关文档片段生成回答"""
    chunks_str = "\n\n".join(chunks)
    prompt = f"""
你是一位知识助手，请根据用户的问题和下列片段生成准确的回答,如果用户的提问与片段无关，请忽略相关片段，正常回答即可。
用户问题: {query}
相关片段：{chunks_str}
    """
    response = ollama.generate(
        model='gemma3:1b',
        prompt=prompt
    )
    return response.response

def init(file_path: str = DB_PATH) -> None:
    """
    初始化知识库
    """
    chunks = split_into_chunks(file_path)
    embeddings = [embed_chunk(chunk) for chunk in chunks]
    save_embeddings(chunks, embeddings)

def show_ollama_modle_list() -> None:
    print(model["model"] for model in ollama.list()["models"])

if __name__ == "__main__":
    init()
    show_ollama_modle_list()
    while True:
        user_input = input("请输入问题：")
        if user_input.lower() == 'exit':
            break;
        retrieved_chunks = retrieve(user_input, 5)
        rerank_chunks = rerank(user_input, retrieved_chunks, 3)
        print(generate(user_input, rerank_chunks))