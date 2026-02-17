
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useOutletContext } from 'react-router-dom';
import QueryPage from './pages/QueryPage';
import ResultsPage from './pages/ResultsPage';
import SignIn from './pages/SignIn';
import SignUp from './pages/SignUp';
import Layout from './components/Layout';
import { AuthProvider } from './context/AuthContext';
import { api } from './api/client';

function Home() {
    const [result, setResult] = useState(null);
    const [queryText, setQueryText] = useState('');

    // We can access engineStatus from Layout via valid react-router context or passing props, 
    // but simpler to just manage query state here for now.

    return result ? (
        <ResultsPage
            result={result}
            queryText={queryText}
            onBack={() => setResult(null)}
            onNewQuery={(q) => { setResult(null); setQueryText(q); }}
        />
    ) : (
        <QueryPage
            onResults={(res, q) => { setResult(res); setQueryText(q); }}
            initialQuery={queryText}
        />
    );
}

function App() {
    const [engineStatus, setEngineStatus] = useState(null); // null = checking, true = online, false = offline

    // Poll engine health every 15 seconds
    useEffect(() => {
        const checkHealth = () => {
            api.checkHealth()
                .then(() => setEngineStatus(true))
                .catch(() => setEngineStatus(false));
        };
        checkHealth();
        const interval = setInterval(checkHealth, 15000);
        return () => clearInterval(interval);
    }, []);

    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Layout engineStatus={engineStatus} />}>
                        <Route index element={<Home />} />
                        <Route path="signin" element={<SignIn />} />
                        <Route path="signup" element={<SignUp />} />
                    </Route>
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
