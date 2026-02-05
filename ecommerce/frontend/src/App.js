import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    // Python service on port 8000
    axios.get('http://localhost:8000/products')
      .then(res => setProducts(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Qyro Ecommerce</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        {products.map(p => (
          <div key={p.id} style={{ border: '1px solid #ccc', padding: '1rem' }}>
            <h2>{p.name}</h2>
            <p>${p.price}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
export default App;