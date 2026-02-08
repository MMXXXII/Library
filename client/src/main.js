import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'bootstrap-icons/font/bootstrap-icons.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle'
import axios from 'axios'
import Cookies from 'js-cookie'

axios.defaults.baseURL = '/api'
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'
axios.defaults.withCredentials = true
axios.interceptors.request.use(function (config) {
  config.headers['X-CSRFToken'] = Cookies.get('csrftoken')
  return config
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
