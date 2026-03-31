<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()

const loans = ref([])
const books = ref([])
const members = ref([])
const libraries = ref([])
const loanStats = ref(null)
const searchQuery = ref('')

const formId = ref(null)
const formLibrary = ref(null)
const formBook = ref(null)
const formMember = ref(null)
const formReturnDate = ref('')
const showModal = ref(false)

const filteredLoans = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return loans.value
  return loans.value.filter(loan =>
    loan.book_title.toLowerCase().includes(q) ||
    loan.member_name.toLowerCase().includes(q)
  )
})

const availableBooks = computed(() => {
  return books.value.filter(b => {
    if (!b.is_available) return false
    if (formLibrary.value && b.library !== formLibrary.value) return false
    return true
  })
})

function resetForm() {
  formId.value = null
  formLibrary.value = null
  formBook.value = null
  formMember.value = null
  formReturnDate.value = ''
}

async function loadData() {
  const booksRes = await axios.get('/books/')
  books.value = booksRes.data
  const membersRes = await axios.get('/members/')
  members.value = membersRes.data
  const librariesRes = await axios.get('/libraries/')
  libraries.value = librariesRes.data
  const loansRes = await axios.get('/loans/')
  for (let i = 0; i < loansRes.data.length; i++) {
    const loan = loansRes.data[i]
    const book = books.value.find(b => b.id === loan.book)
    const member = members.value.find(m => m.id === loan.member)

    if (book) {
      loan.book_title = book.title
    } else {
      loan.book_title = ''
    }

    if (member) {
      loan.member_name = member.username
    } else {
      loan.member_name = 'Неизвестно'
    }

    if (book) {
      const library = libraries.value.find(l => l.id === book.library)
      if (library) {
        loan.library_name = library.name
      } else {
        loan.library_name = ''
      }
    } else {
      loan.library_name = ''
    }

    if (loan.return_date) {
      loan.status = 'Возвращена'
    } else {
      loan.status = 'Выдана'
    }
  }
  loans.value = loansRes.data
  const statsRes = await axios.get('/loans/stats/')
  loanStats.value = statsRes.data
}

function openAddModal() {
  resetForm()
  showModal.value = true
}

function openEdit(loan) {
  const book = books.value.find(b => b.id === loan.book)
  formId.value = loan.id
  formLibrary.value = book ? book.library : null
  formBook.value = loan.book
  formMember.value = loan.member
  formReturnDate.value = loan.return_date
  showModal.value = true
}

function closeModal() {
  resetForm()
  showModal.value = false
}

async function saveForm() {
  if (!formBook.value) return
  const data = { book: formBook.value, loan_date: formReturnDate.value }
  if (formMember.value) data.member = formMember.value
  if (formId.value) {
    await axios.put('/loans/' + formId.value + '/', data)
  } else {
    await axios.post('/loans/', data)
  }
  closeModal()
  await loadData()
}

async function deleteLoan(loan) {
  if (!confirm(`Вы точно хотите удалить выдачу книги "${loan.book_title}"?`)) return
  await axios.delete('/loans/' + loan.id + '/')
  await loadData()
}

async function returnBook(loan) {
  await axios.post('/loans/' + loan.id + '/return/')
  await loadData()
}

async function exportLoans() {
  const res = await axios.get('/loans/export/', { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'Loans.xlsx'
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
        <p>Всего выдач: {{ loanStats ? loanStats.count : 0 }}</p>
        <p>Читатель с максимальным количеством книг: {{ loanStats && loanStats.topReader ? loanStats.topReader.name : 'не найден' }}</p>
      </div>
      <div class="col-auto d-flex gap-2">
        <button v-if="userStore.isSuperUser" class="btn btn-primary" @click="openAddModal">Добавить выдачу</button>
        <button class="btn btn-outline-success" @click="exportLoans">Экспорт Excel</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input type="text" class="form-control" placeholder="Поиск по книге или читателю" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="loan in filteredLoans" :key="loan.id"
        class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <div>{{ loan.book_title }}</div>
          <div class="text-muted small">
            Читатель: {{ loan.member_name }} | Библиотека: {{ loan.library_name }} | Дата: {{ loan.loan_date }} |
            Статус: {{ loan.status }}
          </div>
        </div>
        <div class="d-flex gap-2">
          <button v-if="!loan.return_date" class="btn btn-warning btn-sm" @click="returnBook(loan)">
            <i class="bi bi-arrow-return-left"></i>
          </button>
          <button class="btn btn-success btn-sm" v-if="userStore.isSuperUser" @click="openEdit(loan)">
            <i class="bi bi-pen-fill"></i>
          </button>
          <button class="btn btn-danger btn-sm" v-if="userStore.isSuperUser" @click="deleteLoan(loan)">
            <i class="bi bi-x"></i>
          </button>
        </div>
      </li>
      <li v-if="filteredLoans.length === 0" class="list-group-item text-center text-muted">
        Выдач пока нет
      </li>
    </ul>

    <div v-if="showModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ formId ? 'Редактировать выдачу' : 'Добавить выдачу' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body d-flex flex-column gap-2">
            <select class="form-select" v-model="formLibrary" @change="formBook = null">
              <option value="">Библиотека</option>
              <option v-for="l in libraries" :key="l.id" :value="l.id">{{ l.name }}</option>
            </select>
            <select class="form-select" v-model="formBook">
              <option value="">Книга</option>
              <option v-for="b in availableBooks" :key="b.id" :value="b.id">{{ b.title }}</option>
            </select>
            <select class="form-select" v-model="formMember">
              <option value="">Читатель</option>
              <option v-for="m in members" :key="m.id" :value="m.id">{{ m.username }}</option>
            </select>
            <label class="form-label mb-0">Дата возврата книги</label>
            <input type="date" class="form-control" v-model="formReturnDate">
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