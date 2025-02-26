<template>
  <div class="page-wrapper">
    <div class="unet-container">
      <div class="header">
        <h2 class="page-title">车辆零部件缺陷检测系统</h2>
        <div class="header-buttons">
          <el-button type="primary" @click="goToLogin" class="admin-button">后台</el-button>
        </div>
      </div>
      
      <el-card class="upload-card">
        <div class="input-section">
          <el-radio-group v-model="inputMethod" class="input-method-group">
            <el-radio label="upload">上传新文件</el-radio>
            <el-radio label="camera">拍摄照片</el-radio>
            <el-radio label="select">选择已有数据集</el-radio>
          </el-radio-group>

          <!-- 上传新文件部分 -->
          <el-upload
            v-if="inputMethod === 'upload'"
            class="upload-demo"
            drag
            action=""
            :auto-upload="false"
            :on-change="handleFileChange"
            accept="image/*,.zip"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽图片或ZIP文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">支持上传单张图片或包含多张图片的ZIP文件</div>
            </template>
          </el-upload>

          <!-- 摄像头拍照部分 -->
          <div v-if="inputMethod === 'camera'" class="camera-section">
            <div class="camera-container">
              <video 
                ref="videoElement" 
                class="camera-preview"
                :class="{ 'hidden': hasPhoto }"
                autoplay 
                playsinline
              ></video>
              <canvas 
                ref="photoCanvas" 
                class="photo-canvas"
                :class="{ 'visible': hasPhoto }"
              ></canvas>
            </div>
            <div class="camera-controls">
              <el-button 
                v-if="!hasPhoto"
                type="primary" 
                @click="takePhoto"
                :disabled="!isCameraReady"
                class="camera-button"
              >
                拍照
              </el-button>
              <template v-else>
                <el-button type="primary" @click="retakePhoto" class="camera-button">
                  重新拍摄
                </el-button>
                <el-button type="success" @click="usePhoto" class="camera-button">
                  使用照片
                </el-button>
              </template>
            </div>
          </div>

          <!-- 选择已有数据集部分 -->
          <div v-if="inputMethod === 'select'" class="dataset-select">
            <el-select
              v-model="selectedDataset"
              placeholder="请选择数据集"
              class="dataset-selector"
              filterable
            >
              <el-option
                v-for="dataset in datasetList"
                :key="dataset.id"
                :label="dataset.name"
                :value="dataset.id"
              />
            </el-select>
          </div>
        </div>

        <div class="params-section" v-if="selectedFile || selectedDataset">
          <el-form :model="params" label-width="100px">
            <el-form-item label="缩放因子">
              <el-input-number
                v-model="params.scaleFactor"
                :min="0.1"
                :max="2"
                :step="0.1"
                class="custom-input-number"
              />
            </el-form-item>
            <el-form-item label="预测阈值">
              <el-input-number
                v-model="params.threshold"
                :min="0"
                :max="1"
                :step="0.1"
                class="custom-input-number"
              />
            </el-form-item>
          </el-form>

          <el-button type="primary" @click="handlePredict" :loading="loading" class="predict-button">
            开始预测
          </el-button>
        </div>
      </el-card>

      <el-card v-if="resultUrls.length > 0" class="result-card">
        <template #header>
          <div class="card-header">
            <span>预测结果</span>
            <div class="result-pagination" v-if="resultUrls.length > 1">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="1"
                :total="resultUrls.length"
                layout="prev, pager, next"
                @current-change="handlePageChange"
              />
            </div>
          </div>
        </template>
        <div class="result-image">
          <img :src="currentResultUrl" alt="预测结果" />
        </div>
      </el-card>

      <el-dialog v-model="errorVisible" title="错误" width="30%">
        <span>{{ errorMessage }}</span>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="errorVisible = false">确定</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, computed, watch, onUnmounted } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { predictImage, getDatasetList } from '/@/api/unet'
import { useRouter } from 'vue-router'
import type { UploadFile } from 'element-plus'
import { Session } from '/@/utils/storage'

const router = useRouter()

// 输入方式：上传新文件、拍摄照片或选择已有数据集
const inputMethod = ref<'upload' | 'camera' | 'select'>('upload')
const selectedFile = ref<UploadFile>()
const selectedDataset = ref<number>()
const datasetList = ref<Array<{id: number, name: string, data: string}>>([])
const loading = ref(false)
const resultUrls = ref<string[]>([])
const currentPage = ref(1)
const errorVisible = ref(false)
const errorMessage = ref('')

// 摄像头相关
const videoElement = ref<HTMLVideoElement | null>(null)
const photoCanvas = ref<HTMLCanvasElement | null>(null)
const stream = ref<MediaStream | null>(null)
const hasPhoto = ref(false)
const isCameraReady = ref(false)

// 监听输入方式的变化
watch(inputMethod, async (newValue, oldValue) => {
  if (newValue === 'select') {
    // 切换到数据集选择模式时，重新加载数据集列表
    await loadDatasetList()
  } else if (newValue === 'camera') {
    // 切换到摄像头模式时，初始化摄像头
    await initCamera()
  } else if (oldValue === 'camera') {
    // 从摄像头模式切换出去时，关闭摄像头
    closeCamera()
  }
  // 清除之前的选择
  selectedFile.value = undefined
  selectedDataset.value = undefined
  resultUrls.value = []
  hasPhoto.value = false
})

const currentResultUrl = computed(() => {
  if (resultUrls.value.length === 0) return ''
  return resultUrls.value[currentPage.value - 1]
})

const params = reactive({
  scaleFactor: 1.0,
  threshold: 0.5
})

// 初始化摄像头
const initCamera = async () => {
  try {
    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'environment' // 优先使用后置摄像头
      }
    })
    
    if (videoElement.value) {
      videoElement.value.srcObject = stream.value
      isCameraReady.value = true
    }
  } catch (err: any) {
    errorMessage.value = '无法访问摄像头：' + (err.message || '未知错误')
    errorVisible.value = true
    inputMethod.value = 'upload'
  }
}

// 关闭摄像头
const closeCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
  isCameraReady.value = false
}

// 拍照
const takePhoto = () => {
  if (videoElement.value && photoCanvas.value) {
    const context = photoCanvas.value.getContext('2d')
    if (context) {
      photoCanvas.value.width = videoElement.value.videoWidth
      photoCanvas.value.height = videoElement.value.videoHeight
      context.drawImage(videoElement.value, 0, 0)
      hasPhoto.value = true
    }
  }
}

// 重新拍照
const retakePhoto = () => {
  hasPhoto.value = false
}

// 使用拍摄的照片
const usePhoto = () => {
  if (photoCanvas.value) {
    photoCanvas.value.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], 'camera-photo.jpg', { type: 'image/jpeg' })
        const uploadFile: UploadFile = {
          name: file.name,
          raw: file,
          uid: Date.now().toString(),
          status: 'ready'
        }
        selectedFile.value = uploadFile
      }
    }, 'image/jpeg', 0.95)
  }
}

const handleFileChange = (file: UploadFile) => {
  // 检查文件类型
  const isImage = file.raw?.type.startsWith('image/')
  const isZip = file.raw?.type === 'application/zip' || file.name.endsWith('.zip')
  
  if (!isImage && !isZip) {
    errorMessage.value = '请上传图片文件或ZIP文件'
    errorVisible.value = true
    selectedFile.value = undefined
    return
  }
  
  selectedFile.value = file
  selectedDataset.value = undefined
  resultUrls.value = [] // 清空之前的结果
  currentPage.value = 1
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const handlePredict = async () => {
  if (!selectedFile.value && !selectedDataset.value) {
    errorMessage.value = '请选择文件或数据集'
    errorVisible.value = true
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('scale_factor', params.scaleFactor.toString())
    formData.append('threshold', params.threshold.toString())

    if (selectedFile.value) {
      formData.append('file', selectedFile.value.raw!)
    } else if (selectedDataset.value) {
      const dataset = datasetList.value.find(d => d.id === selectedDataset.value)
      if (dataset) {
        formData.append('data', dataset.data)
      }
    }

    const response = await predictImage(formData)
    
    if (Array.isArray(response.result_urls)) {
      resultUrls.value = response.result_urls
    } else {
      resultUrls.value = [response.result_url]
    }
    currentPage.value = 1
  } catch (error: any) {
    errorMessage.value = error.message || '预测失败'
    errorVisible.value = true
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/home')
}

const loadDatasetList = async () => {
  try {
    const response = await getDatasetList()
    if (response.data) {
      datasetList.value = response.data.results || response.data
    }
  } catch (error: any) {
    console.error('加载数据集列表失败:', error)
    errorMessage.value = '加载数据集列表失败：' + (error.response?.data?.msg || error.message)
    errorVisible.value = true
    // 如果是认证错误，切换回上传模式
    if (error.response?.data?.code === 4000) {
      inputMethod.value = 'upload'
    }
  }
}

onMounted(async () => {
  // 初始化状态
  selectedFile.value = undefined
  selectedDataset.value = undefined
  resultUrls.value = []
  currentPage.value = 1
  loading.value = false
  errorVisible.value = false
  errorMessage.value = ''
  params.scaleFactor = 1.0
  params.threshold = 0.5
  
  // 加载数据集列表
  await loadDatasetList()
})

onUnmounted(() => {
  // 组件卸载时关闭摄像头
  closeCamera()
})
</script>

<style>
:root, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow-y: auto !important;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
</style>

<style scoped>
.page-wrapper {
  flex: 1;
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(to bottom, #f8f9fa, #ffffff);
  overflow-y: auto;
}

.unet-container {
  box-sizing: border-box;
  padding: 30px;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 0 20px;
}

.page-title {
  font-size: 28px;
  color: #2c3e50;
  font-weight: 600;
  margin: 0;
  background: linear-gradient(120deg, #2c3e50, #3498db);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-buttons {
  display: flex;
  align-items: center;
}

.admin-button {
  font-weight: 500;
  padding: 10px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.admin-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
}

.upload-card {
  margin-bottom: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.input-method-group {
  margin-bottom: 20px;
}

.camera-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px;
}

.camera-container {
  width: 100%;
  max-width: 800px;
  position: relative;
  aspect-ratio: 16/9;
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
}

.camera-preview, .photo-canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.camera-preview.hidden {
  display: none;
}

.photo-canvas {
  display: none;
}

.photo-canvas.visible {
  display: block;
}

.camera-controls {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 20px;
}

.camera-button {
  min-width: 120px;
  height: 40px;
}

.dataset-select {
  width: 100%;
  text-align: center;
  padding: 20px;
}

.dataset-selector {
  width: 80%;
  max-width: 400px;
}

.upload-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.el-upload {
  width: 100%;
}

.el-upload-dragger {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.el-upload-dragger:hover {
  border-color: #409EFF;
  background-color: rgba(64, 158, 255, 0.05);
}

.el-icon--upload {
  font-size: 48px;
  color: #409EFF;
  margin-bottom: 16px;
}

.el-upload__text {
  font-size: 16px;
  color: #606266;
}

.el-upload__text em {
  color: #409EFF;
  font-style: normal;
  font-weight: 600;
}

.el-upload__tip {
  color: #909399;
  font-size: 14px;
  margin-top: 12px;
  text-align: center;
}

.params-section {
  margin-top: 30px;
  padding: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background-color: #f8f9fa;
  border-radius: 8px;
}

.custom-input-number {
  width: 180px;
}

.predict-button {
  width: 100%;
  margin-top: 20px;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 1px;
  background: linear-gradient(120deg, #409EFF, #36D1DC);
  border: none;
  transition: all 0.3s ease;
}

.predict-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.result-card {
  margin-top: 30px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.result-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.card-header {
  padding: 16px 20px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  background-color: #f8f9fa;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-pagination {
  display: flex;
  align-items: center;
}

.result-image {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.result-image img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.el-card {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>