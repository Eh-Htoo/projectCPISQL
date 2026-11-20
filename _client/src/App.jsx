import { useState, useEffect } from 'react'
import heroImg from './assets/hero.png'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import './App.css'
import axios from 'axios'
function App() {
  const [count, setCount] = useState(0)
  const [array, setArray] = useState([])



  const fetchAPI = async () => {
    const response = await axios.get("http://127.0.0.1:8080/api/users")
    setArray(response.data.users)
  }

  useEffect(() => {
    fetchAPI()
  }, [])


  return (
    <>
     <p>  {
              array.map((user, index) => (
                <span key = {index}> {user }</span>
              ))
            }</p>
    </>
  )
}

export default App
