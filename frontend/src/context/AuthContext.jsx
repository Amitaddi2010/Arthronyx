
import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    // BYPASS AUTH: Set dummy user immediately
    const [user, setUser] = useState({
        email: 'bypass@arthronyx.internal',
        full_name: 'Bypass User'
    });
    const [loading, setLoading] = useState(false); // No loading needed

    useEffect(() => {
        const initAuth = async () => {
            const token = localStorage.getItem('arthronyx_token');
            if (token) {
                try {
                    // Token exists, fetch user profile
                    const response = await apiClient.get('/auth/me');
                    setUser(response.data);
                } catch (error) {
                    // Token invalid or expired
                    console.error('Session expired:', error);
                    localStorage.removeItem('arthronyx_token');
                    setUser(null);
                }
            }
            setLoading(false);
        };
        initAuth();
    }, []);

    const login = async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        try {
            const response = await apiClient.post('/auth/token', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });
            const { access_token } = response.data;

            localStorage.setItem('arthronyx_token', access_token);

            // Fetch user details immediately after login
            const userResponse = await apiClient.get('/auth/me');
            setUser(userResponse.data);
            return userResponse.data;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    };

    const signup = async (name, email, password) => {
        try {
            await apiClient.post('/auth/signup', {
                email,
                password,
                full_name: name,
            });
            // Auto-login after signup
            return await login(email, password);
        } catch (error) {
            console.error('Signup failed:', error);
            throw error;
        }
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('arthronyx_token');
        // Optional: Redirect to login page is handled by protected routes or UI logic
    };

    return (
        <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
