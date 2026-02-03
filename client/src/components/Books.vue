<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)

const books = ref([])
const genres = ref([])
const libraries = ref([])
const bookStats = ref(null)

const searchQuery = ref('')
const formId = ref(null)
const formTitle = ref('')
const formGenre = ref('')
const formLibrary = ref('')
const formFile = ref(null)

const filteredBooks = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return books.value
  return books.value.filter(b => (b.title || '').toLowerCase().includes(q))
})

async function loadData() {
  const [booksRes, statsRes, genresRes, libsRes] = await Promise.all([
    axios.get('/books/'),
    axios.get('/books/stats/'),
    axios.get('/genres/'),
    axios.get('/libraries/')
  ])

  books.value = booksRes.data.map(b => ({
    ...b,
    genre_name: b.genre_name || b.genre?.name || '',
    library_name: b.library_name || b.library?.name || '',
    status: b.is_available ? 'Доступна' : 'Выдана'
  }))
  bookStats.value = statsRes.data
  genres.value = genresRes.data
  libraries.value = libsRes.data
}

function resetForm() {
  formId.value = null
  formTitle.value = ''
  formGenre.value = ''
  formLibrary.value = ''
  formFile.value = null
}

function editBook(book) {
  formId.value = book.id
  formTitle.value = book.title
  formGenre.value = book.genre?.id || book.genre
  formLibrary.value = book.library?.id || book.library
}

async function saveForm() {
  if (!formTitle.value || !formGenre.value || !formLibrary.value) return

  const payload = {
    title: formTitle.value,
    genre: formGenre.value,
    library: formLibrary.value
  }

  if (formId.value) {
    await axios.put(`/books/${formId.value}/`, payload)
  } else {
    await axios.post('/books/', payload)
  }

  resetForm()
  await loadData()
}

async function deleteBook(book) {
  if (!confirm(`Удалить ${book.title}?`)) return
  await axios.delete(`/books/${book.id}/`)
  await loadData()
}

async function exportFile() {
  const res = await axios.get('/books/export/', {
    params: { type: 'excel' },
    responseType: 'blob'
  })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'Books.xlsx'
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
        <p>Всего книг: {{ bookStats?.count || 0 }}</p>
        <p>Самая популярная: {{ bookStats?.most_borrowed?.title || 'нет данных' }}</p>
      </div>
      <div class="col-auto">
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>


    <div v-if="isAdmin" class="row g-2 mb-3">
      <div class="col">
        <input type="text" class="form-control" placeholder="Название книги" v-model="formTitle">
      </div>
      <div class="col">
        <select class="form-select" v-model="formGenre">
          <option value="">Жанр</option>
          <option v-for="g in genres" :key="g.id" :value="g.id">{{ g.name }}</option>
        </select>
      </div>
      <div class="col">
        <select class="form-select" v-model="formLibrary">
          <option value="">Библиотека</option>
          <option v-for="l in libraries" :key="l.id" :value="l.id">{{ l.name }}</option>
        </select>
      </div>
      <div class="col">
        <input type="file" class="form-control" @change="e => formFile.value = e.target.files[0]">
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="saveForm">{{ formId ? 'Сохранить' : 'Добавить' }}</button>
      </div>
    </div>


    <div class="row mb-3">
      <div class="col">
        <input type="text" class="form-control" placeholder="Поиск по названию" v-model="searchQuery">
      </div>
    </div>


    <ul class="list-group">
      <li v-for="book in filteredBooks" :key="book.id" class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <div>{{ book.title }}</div>
          <div class="text-muted small">
            Жанр: {{ book.genre_name }} | Библиотека: {{ book.library_name }} | Статус: {{ book.status }}
          </div>
        </div>
        <div v-if="isAdmin" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="editBook(book)">
            <i class="bi bi-pen-fill"></i>
          </button>
          <button class="btn btn-danger btn-sm" @click="deleteBook(book)">
            <i class="bi bi-x"></i>
          </button>
        </div>
      </li>
      <li v-if="!filteredBooks.length" class="list-group-item text-center text-muted">
        Книг пока нет
      </li>
    </ul>

  </div>
</template>
