<script setup>
import { ref, onMounted } from 'vue'
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
const formLoanDate = ref('')

function getFilteredLoans() {
  const loansWithDetails = loans.value.map(loan => {
    const book = books.value.find(b => b.id === loan.book)
    const member = members.value.find(m => m.id === loan.member)
    const library = book ? libraries.value.find(l => l.id === book.library) : null
    
    return {
      ...loan,
      book_title: book ? book.title : '',
      member_name: member ? member.username : 'Неизвестно',
      library_name: library ? library.name : '',
      status: loan.return_date ? 'Возвращена' : 'Выдана'
    }
  })
  
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return loansWithDetails
  return loansWithDetails.filter(loan => {
    return loan.book_title.toLowerCase().includes(q) || 
           loan.member_name.toLowerCase().includes(q)
  })
}

function getAvailableBooks() {
  return books.value.filter(b => {
    if (!b.is_available) return false
    if (formLibrary.value && b.library !== formLibrary.value) return false
    return true
  })
}

function resetForm() {
  formId.value = null
  formLibrary.value = null
  formBook.value = null
  formMember.value = null
  formLoanDate.value = ''
}

async function loadData() {
  const booksRes = await axios.get('/books/')
  books.value = booksRes.data
  const membersRes = await axios.get('/members/')
  members.value = membersRes.data
  const librariesRes = await axios.get('/libraries/')
  libraries.value = librariesRes.data
  const loansRes = await axios.get('/loans/')
  loans.value = loansRes.data
  const statsRes = await axios.get('/loans/stats/')
  loanStats.value = statsRes.data
}

function openEdit(loan) {
  const book = books.value.find(b => b.id === loan.book)
  formId.value = loan.id
  formLibrary.value = book ? book.library : null
  formBook.value = loan.book
  formMember.value = loan.member
  formLoanDate.value = loan.loan_date
}

async function saveForm() {
  if (!formBook.value || !formLoanDate.value) return
  const data = { book: formBook.value, loan_date: formLoanDate.value }
  if (formMember.value) data.member = formMember.value
  if (formId.value) {
    await axios.put('/loans/' + formId.value + '/', data)
  } else {
    await axios.post('/loans/', data)
  }
  resetForm()
  await loadData()
}

async function deleteLoan(loan) {
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

    <div class="row mb-3">
      <div class="col">
        <p>Всего выдач: {{ loanStats ? loanStats.count : 0 }}</p>
        <p>Читатель с максимальным количеством книг: {{ loanStats && loanStats.topReader ? loanStats.topReader.name : 'не найден' }}</p>
      </div>
      <div class="col-auto">
        <button class="btn btn-outline-success" @click="exportLoans">Экспорт Excel</button>
      </div>
    </div>

    <div v-if="userStore.isSuperUser" class="row g-2 mb-3">
      <div class="col">
        <select class="form-select" v-model="formLibrary" @change="formBook = null">
          <option value="">Библиотека</option>
          <option v-for="l in libraries" :key="l.id" :value="l.id">{{ l.name }}</option>
        </select>
      </div>
      <div class="col">
        <select class="form-select" v-model="formBook">
          <option value="">Книга</option>
          <option v-for="b in getAvailableBooks()" :key="b.id" :value="b.id">{{ b.title }}</option>
        </select>
      </div>
      <div class="col">
        <select class="form-select" v-model="formMember">
          <option value="">Читатель</option>
          <option v-for="m in members" :key="m.id" :value="m.id">{{ m.username }}</option>
        </select>
      </div>
      <div class="col">
        <input type="date" class="form-control" v-model="formLoanDate">
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="saveForm">{{ formId ? 'Сохранить' : 'Добавить' }}</button>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <input type="text" class="form-control" placeholder="Поиск по книге или читателю" v-model="searchQuery">
      </div>
    </div>

    <ul class="list-group">
      <li v-for="loan in getFilteredLoans()" :key="loan.id"
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
      <li v-if="getFilteredLoans().length === 0" class="list-group-item text-center text-muted">
        Выдач пока нет
      </li>
    </ul>

  </div>
</template>