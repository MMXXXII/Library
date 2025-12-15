<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const otpCode = ref('')
const showOtpInput = ref(false)
const userEmail = ref('')
const qrCodeImage = ref('')
const totpKey = ref('')

const otpTimer = ref(300)
let timerInterval = null

const formattedOtpTime = computed(() => {
  const m = otpTimer.value / 60 | 0; 
  const s = otpTimer.value % 60;
  return `${m < 10 ? '0' + m : m}:${s < 10 ? '0' + s : s}`;
});

onMounted(() => {
  if (route.path === '/login' && userStore.isAuthenticated && userStore.isOtpVerified) {
    router.push('/books')
  }
})

function startOtpTimer() {
  otpTimer.value = 30;
  timerInterval = setInterval(function() {
    otpTimer.value--;

    if (otpTimer.value <= 0) {
      clearInterval(timerInterval);
      timerInterval = null;
      showOtpInput.value = false;
      otpCode.value = '';
      qrCodeImage.value = '';
      totpKey.value = '';
      userStore.error = 'Время ввода OTP истекло';
    }
  }, 1000);
}

function stopOtpTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

async function handleLogin() {
  const result = await userStore.login(username.value, password.value)
  userEmail.value = result.email
  qrCodeImage.value = result.qr_code
  totpKey.value = result.totp_key
  showOtpInput.value = true
  userStore.error = null
  stopOtpTimer()
  startOtpTimer()
}

async function handleOtpSubmit() {
  const success = await userStore.verifyOtp(otpCode.value)
  if (success) {
    stopOtpTimer()
    username.value = ''
    password.value = ''
    otpCode.value = ''
    showOtpInput.value = false
    qrCodeImage.value = ''
    totpKey.value = ''
    router.push('/books')
  }
}

function handleBack() {
  stopOtpTimer()
  showOtpInput.value = false
  otpCode.value = ''
  username.value = ''
  password.value = ''
  qrCodeImage.value = ''
  totpKey.value = ''
  userStore.error = null
}

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}
</script>


<template>
  <v-container class="profile-container" v-if="$route.path === '/profile'">
    <v-card max-width="600" class="mx-auto my-5 pa-5">
      <v-card-title>Профиль пользователя</v-card-title>
      <v-card-text>
        <v-progress-linear v-if="userStore.loading" indeterminate color="primary"></v-progress-linear>

        <div v-else-if="userStore.user">
          <v-list dense>
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title><strong>Имя пользователя:</strong> {{ userStore.user.username }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title><strong>Email:</strong> {{ userStore.user.email }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list>
          <v-btn color="error" class="mt-4" @click="handleLogout" block>Выход</v-btn>
        </div>

        <v-alert type="error" v-else-if="userStore.error" dense outlined>
          {{ userStore.error }}
        </v-alert>
      </v-card-text>
    </v-card>
  </v-container>

  <v-container max-width="400" class="login-container mx-auto my-5 pa-5" v-else>
    <v-card class="pa-8" elevation="8" rounded="lg">
      <v-form v-if="!showOtpInput" @submit.prevent="handleLogin">
        <v-text-field
          label="Имя пользователя"
          v-model="username"
          required
          autocomplete="username"
          prepend-inner-icon="mdi-account"
          dense
          variant="outlined"
          class="mb-4"
        ></v-text-field>

        <v-text-field
          label="Пароль"
          v-model="password"
          required
          type="password"
          autocomplete="current-password"
          prepend-inner-icon="mdi-lock"
          dense
          variant="outlined"
        ></v-text-field>

        <v-btn 
          type="submit" 
          :loading="userStore.loading" 
          :disabled="userStore.loading" 
          color="primary" 
          block
          size="large"
          class="mt-6"
          rounded="lg"
        >
          {{ userStore.loading ? 'Загрузка...' : 'Далее' }}
        </v-btn>
      </v-form>

      <v-form v-else @submit.prevent="handleOtpSubmit">
        <v-alert type="info" border="left" prominent class="mb-6">
          <v-row>
            <v-col cols="12">
              <strong>Введите код подтверждения</strong>
            </v-col>
            <v-col cols="12">
              Осталось времени: <strong>{{ formattedOtpTime }}</strong>
            </v-col>
          </v-row>
        </v-alert>

        <div v-if="qrCodeImage" class="text-center mb-4">
          <img :src="qrCodeImage" alt="QR Code" style="max-width: 100%; height: auto;">
          <div class="mt-3">
            <small>Отсканируйте QR-код в Google Authenticator</small>
          </div>
          <div class="mt-2">
            <small>Или введите ключ вручную:</small>
            <div class="mt-1" style="word-break: break-all; font-family: monospace; font-size: 12px;">
              {{ totpKey }}
            </div>
          </div>
        </div>

        <v-text-field
          label="Код подтверждения"
          v-model="otpCode"
          type="text"
          maxlength="6"
          inputmode="numeric"
          required
          prepend-inner-icon="mdi-cellphone"
          dense
          variant="outlined"
        ></v-text-field>

        <v-btn
          type="submit"
          :loading="userStore.loading"
          :disabled="userStore.loading || otpCode.length !== 6"
          color="primary"
          block
          size="large"
          class="mt-4"
          rounded="lg"
        >
          {{ userStore.loading ? 'Проверка...' : 'Подтвердить' }}
        </v-btn>

        <v-btn
          type="button"
          class="mt-2"
          color="secondary"
          @click="handleBack"
          :disabled="userStore.loading"
          block
          size="large"
          variant="outlined"
          rounded="lg"
        >
          Назад
        </v-btn>
      </v-form>

      <v-alert v-if="userStore.error" type="error" dense outlined class="mt-6" rounded="lg">
        {{ userStore.error }}
      </v-alert>
    </v-card>
  </v-container>
</template>