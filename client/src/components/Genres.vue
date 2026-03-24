<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const genres = ref([])
const genreStats = ref(null)
const searchQuery = ref('')
const formId = ref(null)
const formName = ref('')

function getFilteredGenres() {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) 
    return genres.value
  const out = []
  for (let i = 0; i < genres.value.length; i++) {
    const g = genres.value[i]
    const name = g.name || ''
    if (name.toLowerCase().indexOf(q) !== -1) out.push(g)
  }
  return out
}

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

function editGenre(genre) {
  formId.value = genre.id
  formName.value = genre.name
}

async function saveForm() {
  if (!formName.value) return
  const payload = { name: formName.value }
  if (formId.value) {
    await axios.put('/genres/' + formId.value + '/', payload)
  } else {
    await axios.post('/genres/', payload)
  }
  resetForm()
  await loadData()
}

async function deleteGenre(genre) {
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

    <div class="row mb-3">
      <div class="col">
        <p>Всего: {{ genreStats ? genreStats.count : 0 }}</p>
        <p>Самый популярный: {{ genreStats ? genreStats.top || 'нет данных' : 'нет данных' }}</p>
      </div>
      <div class="col-auto" v-if="userStore.isSuperUser">
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div v-if="userStore.isSuperUser" class="row g-2 mb-3">
      <div class="col">
        <input class="form-control" placeholder="Название жанра" v-model="formName">
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="saveForm">{{ formId ? 'Сохранить' : 'Добавить' }}</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input class="form-control" placeholder="Поиск" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="genre in getFilteredGenres()" :key="genre.id" class="list-group-item d-flex justify-content-between align-items-center">
        <div>{{ genre.name }}</div>
        <div v-if="userStore.isSuperUser" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="editGenre(genre)"><i class="bi bi-pen-fill"></i></button>
          <button class="btn btn-danger btn-sm" @click="deleteGenre(genre)"><i class="bi bi-x"></i></button>
        </div>
      </li>
      <li v-if="getFilteredGenres().length === 0" class="list-group-item text-center text-muted">Жанров пока нет</li>
    </ul>

  </div>
</template>
