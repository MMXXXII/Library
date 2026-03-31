<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const libraries = ref([])
const libraryStats = ref(null)
const searchQuery = ref('')
const formId = ref(null)
const formName = ref('')
const showModal = ref(false)

const filteredLibraries = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return libraries.value
  return libraries.value.filter(l => (l.name || '').toLowerCase().includes(q))
})

async function loadData() {
  const libsRes = await axios.get('/libraries/')
  libraries.value = libsRes.data
  const statsRes = await axios.get('/libraries/stats/')
  libraryStats.value = statsRes.data
}

function resetForm() {
  formId.value = null
  formName.value = ''
}

function openAddModal() {
  resetForm()
  showModal.value = true
}

function editLibrary(lib) {
  formId.value = lib.id
  formName.value = lib.name
  showModal.value = true
}

function closeModal() {
  resetForm()
  showModal.value = false
}

async function saveForm() {
  if (!formName.value) return
  const payload = { name: formName.value }
  if (formId.value) {
    await axios.put('/libraries/' + formId.value + '/', payload)
  } else {
    await axios.post('/libraries/', payload)
  }
  closeModal()
  await loadData()
}

async function deleteLibrary(lib) {
  if (!confirm(`Вы точно хотите удалить библиотеку "${lib.name}"?`)) return
  await axios.delete('/libraries/' + lib.id + '/')
  await loadData()
}

async function exportFile() {
  const res = await axios.get('/libraries/export/', { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'Libraries.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await userStore.fetchUserInfo()
  await loadData()
})
</script>

<template>
  <div class="container mt-4">

    <div class="row mb-3 align-items-center">
      <div class="col">
        <p>Всего библиотек: {{ libraryStats ? libraryStats.count : 0 }}</p>
        <p>Самая популярная: {{ libraryStats ? libraryStats.top || 'нет данных' : 'нет данных' }}</p>
      </div>
      <div class="col-auto d-flex gap-2">
        <button v-if="userStore.isSuperUser" class="btn btn-primary" @click="openAddModal">Добавить библиотеку</button>
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input class="form-control" placeholder="Поиск" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="lib in filteredLibraries" :key="lib.id"
        class="list-group-item d-flex justify-content-between align-items-center">
        <div>{{ lib.name }}</div>
        <div v-if="userStore.isSuperUser" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="editLibrary(lib)"><i class="bi bi-pen-fill"></i></button>
          <button class="btn btn-danger btn-sm" @click="deleteLibrary(lib)"><i class="bi bi-x"></i></button>
        </div>
      </li>
      <li v-if="filteredLibraries.length === 0" class="list-group-item text-center text-muted">Библиотек пока нет</li>
    </ul>

    <div v-if="showModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ formId ? 'Редактировать библиотеку' : 'Добавить библиотеку' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <input class="form-control" placeholder="Название библиотеки" v-model="formName">
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeModal">Отмена</button>
            <button class="btn btn-primary" @click="saveForm">{{ formId ? 'Сохранить' : 'Добавить' }}</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>