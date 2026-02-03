<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)

const libraries = ref([])
const libraryStats = ref(null)
const searchQuery = ref('')

const formId = ref(null)
const formName = ref('')

const filteredLibraries = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return libraries.value
  return libraries.value.filter(lib => (lib.name || '').toLowerCase().includes(q))
})

async function loadData() {
  const [libsRes, statsRes] = await Promise.all([
    axios.get('/libraries/'),
    axios.get('/libraries/stats/')
  ])
  libraries.value = libsRes.data
  libraryStats.value = statsRes.data
}

function resetForm() {
  formId.value = null
  formName.value = ''
}

function editLibrary(lib) {
  if (!isAdmin.value) return
  formId.value = lib.id
  formName.value = lib.name
}

async function saveForm() {
  if (!isAdmin.value || !formName.value) return

  const payload = { name: formName.value }

  if (formId.value) {
    await axios.put(`/libraries/${formId.value}/`, payload)
  } else {
    await axios.post('/libraries/', payload)
  }

  resetForm()
  await loadData()
}

async function deleteLibrary(lib) {
  if (!isAdmin.value) return
  if (!confirm(`Удалить библиотеку "${lib.name}"?`)) return

  await axios.delete(`/libraries/${lib.id}/`)
  await loadData()
}

async function exportFile() {
  if (!isAdmin.value) return

  const res = await axios.get('/libraries/export/', {
    params: { type: 'excel' },
    responseType: 'blob'
  })

  const url = URL.createObjectURL(new Blob([res.data]))
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

    <div class="row mb-3">
      <div class="col">
        <p>Всего библиотек: {{ libraryStats?.count || 0 }}</p>
        <p>Самая популярная: {{ libraryStats?.top || 'нет данных' }}</p>
      </div>
      <div class="col-auto" v-if="isAdmin">
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div v-if="isAdmin" class="row g-2 mb-3">
      <div class="col">
        <input type="text" class="form-control" placeholder="Название библиотеки" v-model="formName">
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="saveForm">{{ formId ? 'Сохранить' : 'Добавить' }}</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input type="text" class="form-control" placeholder="Поиск" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="lib in filteredLibraries" :key="lib.id" class="list-group-item d-flex justify-content-between align-items-center">
        <div>{{ lib.name }}</div>
        <div v-if="isAdmin" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="editLibrary(lib)">
            <i class="bi bi-pen-fill"></i>
          </button>
          <button class="btn btn-danger btn-sm" @click="deleteLibrary(lib)">
            <i class="bi bi-x"></i>
          </button>
        </div>
      </li>
      <li v-if="!filteredLibraries.length" class="list-group-item text-center text-muted">
        Библиотек пока нет
      </li>
    </ul>

  </div>
</template>
