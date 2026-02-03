<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)

const genres = ref([])
const genreStats = ref(null)

const searchQuery = ref('')
const formId = ref(null)
const formName = ref('')

const filteredGenres = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return genres.value
  return genres.value.filter(g => (g.name || '').toLowerCase().includes(q))
})

async function loadData() {
  const [genresRes, statsRes] = await Promise.all([
    axios.get('/genres/'),
    axios.get('/genres/stats/')
  ])
  genres.value = genresRes.data
  genreStats.value = statsRes.data
}

function resetForm() {
  formId.value = null
  formName.value = ''
}

function editGenre(genre) {
  if (!isAdmin.value) return
  formId.value = genre.id
  formName.value = genre.name
}

async function saveForm() {
  if (!isAdmin.value || !formName.value) return

  const payload = { name: formName.value }

  if (formId.value) {
    await axios.put(`/genres/${formId.value}/`, payload)
  } else {
    await axios.post('/genres/', payload)
  }

  resetForm()
  await loadData()
}

async function deleteGenre(genre) {
  if (!isAdmin.value) return
  if (!confirm(`Удалить жанр "${genre.name}"?`)) return

  await axios.delete(`/genres/${genre.id}/`)
  await loadData()
}

async function exportFile() {
  if (!isAdmin.value) return

  const res = await axios.get('/genres/export/', {
    params: { type: 'excel' },
    responseType: 'blob'
  })

  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = 'Genres.xlsx'
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
        <p>Всего: {{ genreStats?.count || 0 }}</p>
        <p>Самый популярный: {{ genreStats?.top || 'нет данных' }}</p>
      </div>
      <div class="col-auto" v-if="isAdmin">
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div v-if="isAdmin" class="row g-2 mb-3">
      <div class="col">
        <input type="text" class="form-control" placeholder="Название жанра" v-model="formName">
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
      <li v-for="genre in filteredGenres" :key="genre.id" class="list-group-item d-flex justify-content-between align-items-center">
        <div>{{ genre.name }}</div>
        <div v-if="isAdmin" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="editGenre(genre)">
            <i class="bi bi-pen-fill"></i>
          </button>
          <button class="btn btn-danger btn-sm" @click="deleteGenre(genre)">
            <i class="bi bi-x"></i>
          </button>
        </div>
      </li>
      <li v-if="!filteredGenres.length" class="list-group-item text-center text-muted">
        Жанров пока нет
      </li>
    </ul>
  </div>
</template>
