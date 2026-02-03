<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)

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

function getBookTitle(id) { return books.value.find(b => b.id === id)?.title || '' }
function getMemberName(id) { return members.value.find(m => m.id === id)?.username || 'Неизвестно' }
function getLibraryName(bookId) { const b = books.value.find(b => b.id === bookId); return libraries.value.find(l => l.id === b?.library)?.name || '' }

function formatLoans(raw) {
  return raw.map(l => ({
    ...l,
    book_title: getBookTitle(l.book),
    member_name: getMemberName(l.member),
    library_name: getLibraryName(l.book),
    status: l.return_date ? 'Возвращена' : 'Выдана'
  }))
}

const filteredLoans = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return loans.value.filter(l => l.book_title.toLowerCase().includes(q) || l.member_name.toLowerCase().includes(q))
})

function availableBooks() { return books.value.filter(b => b.is_available && (!formLibrary.value || b.library === formLibrary.value)) }

function resetForm() { formId.value = null; formLibrary.value = null; formBook.value = null; formMember.value = null; formLoanDate.value = '' }

async function loadData() {
  books.value = (await axios.get('/books/')).data
  members.value = (await axios.get('/members/')).data
  libraries.value = (await axios.get('/libraries/')).data
  const loansRes = await axios.get('/loans/')
  loans.value = formatLoans(loansRes.data)
  loanStats.value = (await axios.get('/loans/stats/')).data
}

function openEdit(loan) {
  if (!isAdmin.value) return
  const book = books.value.find(b => b.id === loan.book)
  formId.value = loan.id
  formLibrary.value = book?.library || null
  formBook.value = loan.book
  formMember.value = loan.member
  formLoanDate.value = loan.loan_date
}

async function saveForm() {
  if (!formBook.value || !formLoanDate.value) return
  const data = { book: formBook.value, loan_date: formLoanDate.value }
  if (isAdmin.value && formMember.value) data.member = formMember.value
  if (formId.value) await axios.put('/loans/' + formId.value + '/', data)
  else await axios.post('/loans/', data)
  resetForm()
  await loadData()
}

async function deleteLoan(loan) {
  if (!isAdmin.value) return
  if (!confirm(`Удалить выдачу "${getBookTitle(loan.book)}" для ${getMemberName(loan.member)}?`)) return
  await axios.delete('/loans/' + loan.id + '/')
  await loadData()
}

async function returnBook(loan) {
  await axios.post('/loans/' + loan.id + '/return/')
  await loadData()
}

async function exportLoans() {
  if (!isAdmin.value) return
  const res = await axios.get('/loans/export/', { params: { type: 'excel' }, responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = 'loans.xlsx'
  a.click()
  window.URL.revokeObjectURL(url)
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
        <p>Всего выдач: {{ loanStats?.count || 0 }}</p>
        <p>Читатель с максимальным количеством книг: {{ loanStats?.topReader?.name || 'не найден' }}</p>
      </div>
      <div class="col-auto">
        <button class="btn btn-outline-success" @click="exportLoans">Экспорт Excel</button>
      </div>
    </div>

    <div v-if="isAdmin" class="row g-2 mb-3">
      <div class="col">
        <select class="form-select" v-model="formLibrary" @change="formBook = null">
          <option value="">Библиотека</option>
          <option v-for="l in libraries" :key="l.id" :value="l.id">{{ l.name }}</option>
        </select>
      </div>
      <div class="col">
        <select class="form-select" v-model="formBook">
          <option value="">Книга</option>
          <option v-for="b in availableBooks()" :key="b.id" :value="b.id">{{ b.title }}</option>
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
          <button class="btn btn-success btn-sm" v-if="isAdmin" @click="openEdit(loan)">
            <i class="bi bi-pen-fill"></i>
          </button>
          <button class="btn btn-danger btn-sm" v-if="isAdmin" @click="deleteLoan(loan)">
            <i class="bi bi-x"></i>
          </button>
        </div>
      </li>
      <li v-if="!filteredLoans.length" class="list-group-item text-center text-muted">
        Выдач пока нет
      </li>
    </ul>


  </div>
</template>
