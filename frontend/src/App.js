import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Upload from './pages/Upload';
import Analytics from './pages/Analytics';
import ModelTraining from './pages/ModelTraining';
import MyDatasets from './pages/MyDatasets';
import DatasetDetail from './pages/DatasetDetail';
import Dashboard from './pages/Dashboard';

const PrivateRoute = ({ children }) => {
  return localStorage.getItem('access') ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="upload" element={<Upload />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="training" element={<ModelTraining />} />
          <Route path="datasets" element={<MyDatasets />} />
          <Route path="datasets/:id" element={<DatasetDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;