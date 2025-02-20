<template>
  <div class="unet-container">
    <div class="header">
      <h2 class="page-title">车辆零部件缺陷检测系统</h2>
      <div class="header-buttons">
        <el-button type="primary" @click="goToLogin" class="admin-button">后台</el-button>
<!--        <el-button type="danger" @click="handleLogout" v-if="Session.get('token')">退出登录</el-button>-->
      </div>
    </div>
    
    <el-card class="upload-card">
      <el-upload
        class="upload-demo"
        drag
        action=""
        :auto-upload="false"
        :on-change="handleFileChange"
        accept="image/*"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽图片到此处或 <em>点击上传</em>
        </div>
      </el-upload>

      <div class="params-section" v-if="selectedFile">
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

    <el-card v-if="resultUrl" class="result-card">
      <template #header>
        <div class="card-header">
          <span>预测结果</span>
        </div>
      </template>
      <div class="result-image">
        <img :src="resultUrl" alt="预测结果" />
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
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { predictImage } from '/@/api/unet'
import { useRouter } from 'vue-router'
import type { UploadFile } from 'element-plus'
import { Session } from '/@/utils/storage'

const router = useRouter()

const selectedFile = ref<UploadFile>()
const loading = ref(false)
const resultUrl = ref('')
const errorVisible = ref(false)
const errorMessage = ref('')

const params = reactive({
  scaleFactor: 1.0,
  threshold: 0.5
})

const handleFileChange = (file: UploadFile) => {
  selectedFile.value = file
}

const handlePredict = async () => {
  if (!selectedFile.value) {
    errorMessage.value = '请先选择图片'
    errorVisible.value = true
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('image', selectedFile.value.raw!)
    formData.append('scale_factor', params.scaleFactor.toString())
    formData.append('threshold', params.threshold.toString())

    const response = await predictImage(formData)
    resultUrl.value = response.result_url
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

const handleLogout = () => {
  Session.clear()
  // 直接刷新页面
  window.location.reload()
}

onMounted(() => {
  // 初始化状态
  selectedFile.value = undefined
  resultUrl.value = ''
  loading.value = false
  errorVisible.value = false
  errorMessage.value = ''
  params.scaleFactor = 1.0
  params.threshold = 0.5
})
</script>

<style scoped>
.unet-container {
  padding: 30px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  background: linear-gradient(to bottom, #f8f9fa, #ffffff);
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

/* 添加过渡动画 */
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