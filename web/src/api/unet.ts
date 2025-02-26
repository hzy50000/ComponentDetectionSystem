import { request } from '/@/utils/service'
import { Session } from '/@/utils/storage'
import { GetList } from '/@/views/data_manager/api'

// 获取当前用户的数据集列表
export const getDatasetList = () => GetList({})

// UNet预测服务
export function predictImage(data: FormData) {
  const token = Session.get('token')
  return request({
    url: '/api/unet/predict/',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data',
      'Authorization': `JWT ${token}`
    }
  })
}