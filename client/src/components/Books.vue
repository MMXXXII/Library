<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()

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

function getFilteredBooks() {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) 
    return books.value
  const out = []
  for (let i = 0; i < books.value.length; i++) {
    const b = books.value[i]
    const title = b.title || ''
    if (title.toLowerCase().indexOf(q) !== -1) out.push(b)
  }
  return out
}

async function loadData() {
  const booksRes = await axios.get('/books/')
  const arr = []
  for (let i = 0; i < booksRes.data.length; i++) {
    const b = booksRes.data[i]
    b.genre_name = b.genre_name || (b.genre && b.genre.name) || ''
    b.library_name = b.library_name || (b.library && b.library.name) || ''
    if (b.is_available) {
      b.status = 'Доступна'
    } else {
      b.status = 'Выдана'
    }
    arr.push(b)
  }

  books.value = arr
  const statsRes = await axios.get('/books/stats/')
  bookStats.value = statsRes.data
  const genresRes = await axios.get('/genres/')
  genres.value = genresRes.data
  const libsRes = await axios.get('/libraries/')
  libraries.value = libsRes.data
}

function resetForm() {
  formId.value = null
  formTitle.value = ''
  formGenre.value = ''
  formLibrary.value = ''
  formFile.value = null
}

function onFileChange(e) {
  formFile.value = e.target.files[0]
}

function editBook(book) {
  formId.value = book.id
  formTitle.value = book.title
  formGenre.value = (book.genre && book.genre.id) || book.genre
  formLibrary.value = (book.library && book.library.id) || book.library
}

async function saveForm() {
  if (!formTitle.value || !formGenre.value || !formLibrary.value)
    return
  const payload = { title: formTitle.value, genre: formGenre.value, library: formLibrary.value }
  if (formId.value) {
    await axios.put('/books/' + formId.value + '/', payload)
  } else {
    await axios.post('/books/', payload)
  }
  resetForm()
  await loadData()
}

async function deleteBook(book) {
  await axios.delete('/books/' + book.id + '/')
  await loadData()
}

async function exportFile() {
  const res = await axios.get('/books/export/', { responseType: 'blob' })
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
        <p>Всего книг: {{ bookStats ? bookStats.count : 0 }}</p>
        <p>Самая популярная: {{ bookStats?.most_borrowed?.title || 'нет данных' }}
        </p>
      </div>
      <div class="col-auto">
        <button class="btn btn-outline-success" @click="exportFile">Экспорт Excel</button>
      </div>
    </div>

    <div v-if="userStore.isSuperUser" class="row g-2 mb-3">
      <div class="col">
        <input class="form-control" placeholder="Название книги" v-model="formTitle">
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
        <input type="file" class="form-control" @change="onFileChange">
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="saveForm">{{ formId ? 'Сохранить' : 'Добавить' }}</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input class="form-control" placeholder="Поиск по названию" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="book in getFilteredBooks()" :key="book.id"
        class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <div>{{ book.title }}</div>
          <div class="text-muted small">
            Жанр: {{ book.genre_name }} | Библиотека: {{ book.library_name }} | Статус: {{ book.status }}
          </div>
        </div>
        <div v-if="userStore.isSuperUser" class="d-flex gap-2">
          <button class="btn btn-success btn-sm" @click="editBook(book)"><i class="bi bi-pen-fill"></i></button>
          <button class="btn btn-danger btn-sm" @click="deleteBook(book)"><i class="bi bi-x"></i></button>
        </div>
      </li>
      <li v-if="getFilteredBooks().length === 0" class="list-group-item text-center text-muted">Книг пока нет</li>
    </ul>

  </div>
</template>
