import React, { useState } from 'react';
import {
  ExcomProvider,
  Header,
  Navigation,
  PageContainer,
  DataGrid,
  FormField,
  FormSection
} from '@excom-ai/ui-core';
import '@excom-ai/ui-core/dist/styles.css';
import './App.css';
import HelloWorld from './pages/HelloWorld';

function App() {
  const [currentPage, setCurrentPage] = useState('hello');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const config = {
    branding: {
      appTitle: 'Tamkeen ERP',
      orgName: 'Tamkeen Industries',
      logo: '⚡'
    },
    theme: {
      primaryColor: '#00a6fb',
      dangerColor: '#ff4444'
    },
    features: {
      enableAI: true,
      enableChat: true
    }
  };

  const sidebarConfig = {
    hello: {
      title: 'Hello World',
      items: [
        { key: 'main', label: 'Main Page', icon: '👋' }
      ]
    },
    dashboard: {
      title: 'Dashboard',
      items: [
        { key: 'overview', label: 'Overview', icon: '📊' },
        { key: 'analytics', label: 'Analytics', icon: '📈' },
        { key: 'reports', label: 'Reports', icon: '📋' }
      ]
    },
    customers: {
      title: 'Customers',
      items: [
        { key: 'list', label: 'Customer List', icon: '👥' },
        { key: 'add', label: 'Add Customer', icon: '➕' },
        { key: 'orders', label: 'Orders', icon: '📦' }
      ]
    },
    inventory: {
      title: 'Inventory',
      items: [
        { key: 'products', label: 'Products', icon: '📦' },
        { key: 'stock', label: 'Stock Levels', icon: '📊' },
        { key: 'suppliers', label: 'Suppliers', icon: '🚚' }
      ]
    }
  };

  const renderPageContent = () => {
    switch (currentPage) {
      case 'hello':
        return <HelloWorld />;
      case 'dashboard':
        return <DashboardPage />;
      case 'customers':
        return <CustomersPage />;
      case 'inventory':
        return <InventoryPage />;
      default:
        return <HelloWorld />;
    }
  };

  return (
    <ExcomProvider config={config}>
      <div className="App">
        <Header
          user="admin@tamkeen.com"
          currentPage={currentPage}
          onPageChange={setCurrentPage}
        />
        <div className="app-body">
          <Navigation
            sections={Object.entries(sidebarConfig).map(([key, section]) => ({
              id: key,
              title: section.title,
              items: section.items
            }))}
            activeSection={currentPage}
            onNavigate={(section, item) => {
              console.log('Navigate to:', section, item);
              setCurrentPage(section);
            }}
          />
          <PageContainer className={sidebarOpen ? 'with-sidebar' : ''}>
            {renderPageContent()}
          </PageContainer>
        </div>
      </div>
    </ExcomProvider>
  );
}

// Sample pages using ui-core components
function DashboardPage() {
  return (
    <div className="page-container">
      <h1>Dashboard</h1>
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h3>Revenue</h3>
          <p className="metric">$125,430</p>
          <span className="change positive">+12.5%</span>
        </div>
        <div className="dashboard-card">
          <h3>Orders</h3>
          <p className="metric">342</p>
          <span className="change positive">+5.2%</span>
        </div>
        <div className="dashboard-card">
          <h3>Customers</h3>
          <p className="metric">1,243</p>
          <span className="change positive">+8.7%</span>
        </div>
      </div>
    </div>
  );
}

function CustomersPage() {
  const [formData, setFormData] = useState({ name: '', email: '', phone: '' });

  const customers = [
    { id: 1, name: 'Ahmed Al-Rashid', email: 'ahmed@example.com', phone: '+966501234567', status: 'Active' },
    { id: 2, name: 'Fatima Hassan', email: 'fatima@example.com', phone: '+966502345678', status: 'Active' },
    { id: 3, name: 'Omar Khalid', email: 'omar@example.com', phone: '+966503456789', status: 'Inactive' }
  ];

  const columns = [
    { key: 'name', header: 'Name' },
    { key: 'email', header: 'Email' },
    { key: 'phone', header: 'Phone' },
    { key: 'status', header: 'Status' }
  ];

  return (
    <div className="page-container">
      <h1>Customers</h1>

      <FormSection title="Add New Customer">
        <div className="form-row">
          <FormField
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Enter customer name"
          />
          <FormField
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="customer@example.com"
          />
          <FormField
            label="Phone"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder="+966 50 XXX XXXX"
          />
        </div>
        <button
          className="terminal-button primary"
          onClick={() => console.log('Add customer:', formData)}
        >
          Add Customer
        </button>
      </FormSection>

      <div className="table-section">
        <h3>Customer List</h3>
        <DataGrid
          columns={columns}
          data={customers}
          onRowClick={(row) => console.log('Clicked row:', row)}
        />
      </div>
    </div>
  );
}

function InventoryPage() {
  const products = [
    { id: 1, name: 'Widget A', sku: 'WGT-001', stock: 150, price: '$25.00' },
    { id: 2, name: 'Gadget B', sku: 'GDG-002', stock: 75, price: '$45.00' },
    { id: 3, name: 'Device C', sku: 'DVC-003', stock: 200, price: '$15.00' }
  ];

  const columns = [
    { key: 'name', header: 'Product Name' },
    { key: 'sku', header: 'SKU' },
    { key: 'stock', header: 'Stock Level' },
    { key: 'price', header: 'Price' }
  ];

  return (
    <div className="page-container">
      <h1>Inventory Management</h1>
      <DataGrid
        columns={columns}
        data={products}
        onRowClick={(row) => console.log('Product clicked:', row)}
      />
    </div>
  );
}

export default App;
