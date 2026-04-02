import axios from 'axios'

export const getModelConfig = async () => {
  const { data } = await axios.get('/api/models')
  return data
}

export const saveCustomModel = async (payload) => {
  const { data } = await axios.post('/api/models', {
    action: 'save_custom',
    ...payload
  })
  return data
}

export const activateModel = async (modelId) => {
  const { data } = await axios.post('/api/models', {
    action: 'activate',
    model_id: modelId
  })
  return data
}

export const deleteCustomModel = async (modelId) => {
  const { data } = await axios.post('/api/models', {
    action: 'delete_custom',
    model_id: modelId
  })
  return data
}

export const setEmbeddingModel = async (embeddingModelId) => {
  const { data } = await axios.post('/api/models', {
    action: 'set_embedding',
    embedding_model_id: embeddingModelId
  })
  return data
}
