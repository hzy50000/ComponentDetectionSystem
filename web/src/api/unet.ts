import request from '/@/utils/request'

// UNet预测服务
export function predictImage(data: FormData) {
  return request({
    url: '/api/unet/predict/',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}