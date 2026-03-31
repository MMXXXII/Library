<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const genres = ref([])
const genreStats = ref(null)
const searchQuery = ref('')
const formId = ref(null)
const formName = ref('')
const showModal = ref(false)

const filteredGenres = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) 
    return genres.value
  return genres.value.filter(g => (g.name || '').toLowerCase().includes(q))
})

async function loadData() {
  const genresRes = await axios.get('/genres/')
  genres.value = genresRes.data
  const statsRes = await axios.get('/genres/stats/')
  genreStats.value = statsRes.data
}

function resetForm() {
  formId.value = null
  formName.value = ''
}

function openAddModal() {
  resetForm()
  showModal.value = true
}

function editGenre(genre) {
  formId.value = genre.id
  formName.value = genre.name
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
    await axios.put('/genres/' + formId.value + '/', payload)
  } else {
    await axios.post('/genres/', payload)
  }
  closeModal()
  await loadData()
}

async function deleteGenre(genre) {
  if (!confirm(`Вы точно хотите удалить жанр "${genre.name}"?`)) return
  await axios.delete('/genres/' + genre.id + '/')
  await loadData()
}

async function exportFile() {
  const res = await axios.get('/genres/export/', { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
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

    <div class="row mb-3 align-items-center">
      <div class="col">
        <p>Всего: {{ genreStats ? genreStats.count : 0 }}</p>
        <p>Самый популярный: {{ genreStats ? genreStats.top || 'нет данных' : 'нет данных' }}</p>
      </div>
      <div class="col-auto d-flex gap-2">
        <button v-if="userStore.isSuperUser" class="btn btn-primary" @click="openAddModal">Добавить жанр</button>
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input class="form-control" placeholder="Поиск" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="genre in filteredGenres" :key="genre.id"
        class="list-group-item d-flex justify-content-between align-items-center">
        <div>{{ genre.name }}</div>
        <div v-if="userStore.isSuperUser" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="editGenre(genre)"><i class="bi bi-pen-fill"></i></button>
          <button class="btn btn-danger btn-sm" @click="deleteGenre(genre)"><i class="bi bi-x"></i></button>
        </div>
      </li>
      <li v-if="filteredGenres.length === 0" class="list-group-item text-center text-muted">Жанров пока нет</li>
    </ul>

    <div v-if="showModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ formId ? 'Редактировать жанр' : 'Добавить жанр' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <input class="form-control" placeholder="Название жанра" v-model="formName">
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