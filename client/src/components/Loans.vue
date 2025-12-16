<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'


const userStore = useUserStore()
const isAdmin = computed(() => userStore.isSuperUser)
const loans = ref([])
const filteredLoans = ref([])
const loanStats = ref(null)
const books = ref([])
const libraries = ref([])
const members = ref([])
const currentMember = ref(null)


const page = ref(1)
const itemsPerPage = ref(20)


const searchQuery = ref('')
const sortOrder = ref('asc')


const notification = reactive({ visible: false, message: '', type: 'success' })


const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)


const loanToAdd = reactive({ library: null, book: null, member: null, loan_date: '' })
const loanToEdit = reactive({ id: null, library: null, book: null, member: null, loan_date: '' })
const loanToDelete = reactive({ id: null, bookTitle: '', memberName: '' })


function applyFilter() {
  const q = searchQuery.value.trim().toLowerCase()

  const list = loans.value.filter(l => {
    const book = books.value.find(b => b.id === l.book) || {}
    const member = members.value.find(m => m.id === l.member) || {}
    const bookTitle = (book.title || '').toLowerCase()
    const memberName = ((member.first_name || member.username) || '').toLowerCase()

    return bookTitle.includes(q) || memberName.includes(q)
  })

  list.sort((a, b) => {
    const aTitle = (books.value.find(bk => bk.id === a.book)?.title || '').toLowerCase()
    const bTitle = (books.value.find(bk => bk.id === b.book)?.title || '').toLowerCase()
    
    if (sortOrder.value === 'asc') {
      return aTitle.localeCompare(bTitle)
    } else {
      return bTitle.localeCompare(aTitle)
    }
  })

  filteredLoans.value = list
  page.value = 1
}


function getMemberName(id) {
  const mem = members.value.find(m => m.id === id);
  if (!mem) {
    return currentMember.value.first_name || currentMember.value.username || 'Неизвестно';
  }
  return mem.first_name || mem.username || 'Неизвестно';
}


function getLibraryName(bookId) {
  const book = books.value.find(b => b.id === bookId);
  if (!book) {
    return '';
  }
  const lib = libraries.value.find(l => l.id === book.library);
  return lib ? lib.name : '';
}


function getBookTitle(bookId) {
  const book = books.value.find(b => b.id === bookId);
  return book ? book.title : '';
}


function availableBooksToAdd() {
  const library = loanToAdd.library;
  if (!library) {
    return books.value.filter(b => b.is_available);
  }
  return books.value.filter(b => b.is_available && b.library === library);
}


function availableBooksToEdit() {
  const library = loanToEdit.library;
  if (!library) {
    return books.value.filter(b => b.is_available);
  }
  return books.value.filter(b => b.is_available && b.library === library);
}


function onLibraryChange() {
  loanToAdd.book = null;
}


function onEditLibraryChange() {
  loanToEdit.book = null;
}


async function loadCurrentMember() {
  const r = await axios.get('/library-members/')
  if (r.data && r.data.length) {
    if (isAdmin.value) {
      members.value = r.data
    } else {
      currentMember.value = r.data[0]
      members.value = r.data
    }
  }
}


async function loadLibraries() {
  const r = await axios.get('/libraries/')
  libraries.value = r.data
}


async function loadBooks() {
  const r = await axios.get('/books/')
  books.value = r.data
}


async function loadLoans() {
  const r = await axios.get('/loans/');
  
  if (!isAdmin.value && currentMember.value) {
    loans.value = r.data.filter(loan => loan.member === currentMember.value.id);
  } else {
    loans.value = r.data;
  }
  
  applyFilter();
}


async function loadLoanStats() {
  const r = await axios.get('/loans/stats/')
  loanStats.value = r.data
}


async function addLoan() {
  if (!loanToAdd.book || !loanToAdd.loan_date) {
    return
  }

  const memberId = isAdmin.value ? loanToAdd.member : currentMember.value?.id;
  
  if (!memberId) {
    return
  }

  await axios.post('/loans/', {
    book: loanToAdd.book,
    member: memberId,
    loan_date: loanToAdd.loan_date
  })
  
  loanToAdd.library = null
  loanToAdd.book = null
  loanToAdd.member = null
  loanToAdd.loan_date = ''
  
  showAddDialog.value = false
  
  await Promise.all([loadBooks(), loadLoans(), loadLoanStats()])
}


function openEditDialog(loan) {
  if (!isAdmin.value) {
    return;
  }

  const book = books.value.find(b => b.id === loan.book);
  
  loanToEdit.id = loan.id;
  loanToEdit.library = book ? book.library : null;
  loanToEdit.book = loan.book;
  loanToEdit.member = loan.member;
  loanToEdit.loan_date = loan.loan_date;
  
  showEditDialog.value = true;
}


async function updateLoan() {
  if (!isAdmin.value || !loanToEdit.id) {
    return;
  }
  const data = {
    book: loanToEdit.book,
    member: loanToEdit.member,
    loan_date: loanToEdit.loan_date
  };
  await axios.put('/loans/${loanToEdit.id}/', data);
  showEditDialog.value = false;
  await Promise.all([loadBooks(), loadLoans(), loadLoanStats()]);
}


function openDeleteDialog(loan) {
  if (!isAdmin.value) {
    return;
  }
  loanToDelete.id = loan.id;
  loanToDelete.bookTitle = getBookTitle(loan.book);
  loanToDelete.memberName = getMemberName(loan.member);
  
  showDeleteDialog.value = true;
}


async function deleteLoan() {
  if (!isAdmin.value || !loanToDelete.id) {
    return;
  }
  await axios.delete('/loans/${loanToDelete.id}/');
  showDeleteDialog.value = false;
  await Promise.all([loadBooks(), loadLoans(), loadLoanStats()]);
}


async function returnBook(loan) {
  await axios.post('/loans/${loan.id}/return/');
  await Promise.all([loadBooks(), loadLoans(), loadLoanStats()]);

}


async function exportLoans(type = 'excel') {
  if (!isAdmin.value) {
    return;
  }

  const res = await axios.get('/loans/export/', { 
    params: { type }, 
    responseType: 'blob' 
  });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.download = type === 'excel' ? 'loans.xlsx' : 'loans.docx';
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}


const paginatedLoans = computed(() => {
  const start = (page.value - 1) * itemsPerPage.value;
  const end = start + itemsPerPage.value;
  return filteredLoans.value.slice(start, end);
});


const totalPages = computed(() => {
  return Math.ceil(filteredLoans.value.length / itemsPerPage.value);
});


onMounted(async () => {
  await userStore.fetchUserInfo()
  await Promise.all([loadLibraries(), loadBooks(), loadCurrentMember()])
  await loadLoans()
  await loadLoanStats()
})
</script>


<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card class="pa-4" elevation="2">
          <div class="d-flex justify-space-between align-center mb-4">
            <div>
              <h2 class="mb-1">Выдачи</h2>
              <div class="text-body-2 text-medium-emphasis">
                Количество: {{ loanStats?.count || 0 }},
                читатель с максимальным количеством книг: {{ loanStats?.topReader?.name || 'не найден' }}
              </div>
            </div>
            <div class="d-flex gap-2">
              <v-btn v-if="isAdmin" color="primary" prepend-icon="mdi-plus" @click="showAddDialog = true">
                Добавить выдачу
              </v-btn>
              <v-btn v-if="isAdmin" color="success" variant="outlined" prepend-icon="mdi-microsoft-excel" @click="exportLoans('excel')">Excel</v-btn>
              <v-btn v-if="isAdmin" color="indigo" variant="outlined" prepend-icon="mdi-file-word" @click="exportLoans('word')">Word</v-btn>
            </div>
          </div>

          <v-alert v-if="notification.visible" :type="notification.type" class="mb-4" variant="tonal" closable>
            {{ notification.message }}
          </v-alert>

          <v-row class="mb-4" align="center" no-gutters>
            <v-col cols="12" md="6" class="pr-2">
              <v-text-field v-model="searchQuery" label="Поиск по выдачам" variant="outlined"
                density="comfortable" clearable prepend-inner-icon="mdi-magnify" @input="applyFilter" />
            </v-col>
            <v-col cols="12" md="6" class="pl-2">
              <v-select v-model="sortOrder" :items="[
                { title: 'От A до Я', value: 'asc' }, { title: 'От Я до A', value: 'desc' }
              ]" item-title="title" item-value="value" label="Сортировка" variant="outlined" density="comfortable"
                @update:model-value="applyFilter" />
            </v-col>
          </v-row>

          <v-row v-if="!isAdmin" class="mb-4" align="end">
            <v-col cols="4">
              <v-select v-model="loanToAdd.library" :items="libraries" item-value="id" item-title="name" label="Библиотека"
                variant="outlined" density="comfortable" hide-details @update:model-value="onLibraryChange" />
            </v-col>
            <v-col cols="4">
              <v-select v-model="loanToAdd.book" :items="availableBooksToAdd()" item-value="id" item-title="title" label="Книга"
                variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="2">
              <v-text-field v-model="loanToAdd.loan_date" type="date" label="Дата выдачи" variant="outlined" density="comfortable"
                hide-details />
            </v-col>
            <v-col cols="2" >
            </v-col>
          </v-row>

          <v-list lines="two">
            <v-list-item v-for="loan in paginatedLoans" :key="loan.id">
              <template #default>
                <div>
                  <div class="font-weight-medium">
                    {{ getBookTitle(loan.book) }} → {{ getMemberName(loan.member) }}
                    <v-chip v-if="loan.return_date" color="success" variant="flat" size="x-small" class="ml-2">
                      Возвращена {{ loan.return_date }}
                    </v-chip>
                    <v-chip v-else color="warning" variant="flat" size="x-small" class="ml-2">Выдана</v-chip>
                  </div>
                  <div class="text-body-2 text-medium-emphasis">Дата выдачи: {{ loan.loan_date }}</div>
                  <div class="text-body-2 text-medium-emphasis">Библиотека: {{ getLibraryName(loan.book) }}</div>
                </div>
              </template>
              <template #append>
                <div class="d-flex gap-2">
                  <v-btn v-if="!loan.return_date" size="small" variant="text" color="info" prepend-icon="mdi-keyboard-return"
                    @click.stop="returnBook(loan)">
                    Вернуть
                  </v-btn>
                  <v-btn v-if="isAdmin" icon size="small" variant="text" color="primary" @click.stop="openEditDialog(loan)">
                    <v-icon icon="mdi-pencil" />
                  </v-btn>
                  <v-btn v-if="isAdmin" icon size="small" variant="text" color="error" @click.stop="openDeleteDialog(loan)">
                    <v-icon icon="mdi-delete" />
                  </v-btn>
                </div>
              </template>
            </v-list-item>

            <v-list-item v-if="!filteredLoans.length" title="Выдач пока нет" subtitle="Добавьте первую выдачу." />
          </v-list>

          <div v-if="totalPages > 1" class="d-flex justify-center mt-4">
            <v-pagination v-model="page" :length="totalPages" :total-visible="7" />
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="showAddDialog" max-width="520">
      <v-card>
        <v-card-title>Добавить выдачу</v-card-title>
        <v-card-text>
          <v-select v-model="loanToAdd.library" :items="libraries" item-value="id" item-title="name" label="Библиотека"
            variant="outlined" density="comfortable" class="mb-3" @update:model-value="onLibraryChange" />
          <v-select v-model="loanToAdd.book" :items="availableBooksToAdd()" item-value="id" item-title="title" label="Книга"
            variant="outlined" density="comfortable" class="mb-3" />
          <v-select v-model="loanToAdd.member" :items="members" item-value="id" item-title="first_name" label="Читатель"
            variant="outlined" density="comfortable" class="mb-3" />
          <v-text-field v-model="loanToAdd.loan_date" type="date" label="Дата выдачи" variant="outlined" density="comfortable" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showAddDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="addLoan">Добавить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-if="isAdmin" v-model="showEditDialog" max-width="520">
      <v-card>
        <v-card-title>Редактировать выдачу</v-card-title>
        <v-card-text>
          <v-select v-model="loanToEdit.library" :items="libraries" item-value="id" item-title="name" label="Библиотека"
            variant="outlined" density="comfortable" class="mb-3" @update:model-value="onEditLibraryChange" />
          <v-select v-model="loanToEdit.book" :items="availableBooksToEdit()" item-value="id" item-title="title" label="Книга"
            variant="outlined" density="comfortable" class="mb-3" />
          <v-select v-model="loanToEdit.member" :items="members" item-value="id" item-title="first_name" label="Читатель"
            variant="outlined" density="comfortable" class="mb-3" />
          <v-text-field v-model="loanToEdit.loan_date" type="date" label="Дата выдачи" variant="outlined" density="comfortable" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showEditDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="updateLoan">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-if="isAdmin" v-model="showDeleteDialog" max-width="420">
      <v-card>
        <v-card-title class="text-h6">Удалить выдачу</v-card-title>
        <v-card-text>
          Вы уверены, что хотите удалить выдачу <strong>{{ loanToDelete.bookTitle }} → {{ loanToDelete.memberName }}</strong>?
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showDeleteDialog = false">Отмена</v-btn>
          <v-btn color="error" @click="deleteLoan">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>