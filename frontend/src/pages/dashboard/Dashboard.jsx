import React from 'react';
import './Dashboard.css';

const mockData = {
  fleetUtilization: 85,
  activeTrips: 124,
  driversOnDuty: 98,
  pendingAlerts: 5,
  fleetActivity: [
    { id: 1, vehicleId: 'BUS-1034', route: 'Route 17', driver: 'John Doe', status: 'On Time', lastStop: 'Central Station' },
    { id: 2, vehicleId: 'TAXI-502', route: 'City Center', driver: 'Jane Smith', status: 'Delayed', lastStop: 'Market Square' },
    { id: 3, vehicleId: 'AUTO-001', route: 'Route 5', driver: 'Bob Wilson', status: 'On Time', lastStop: 'University' },
    { id: 4, vehicleId: 'MINI-205', route: 'Airport Shuttle', driver: 'Alice Brown', status: 'On Time', lastStop: 'Terminal 2' },
  ],
  maintenanceAlerts: [
    { id: 1, vehicleId: 'BUS-1034', issue: 'Brake wear detected', priority: 'High', dueDate: '2026-08-05' },
    { id: 2, vehicleId: 'TAXI-502', issue: 'Oil change due', priority: 'Medium', dueDate: '2026-08-10' },
  ],
  aiInsights: [
    { id: 1, title: 'Demand Spike Predicted', description: 'Route 17 expected 42% increase in passengers 8-10 AM', recommendation: 'Add 2 buses' },
    { id: 2, title: 'Fuel Efficiency Opportunity', description: 'Vehicle BUS-1034 shows 15% better mileage than fleet average', recommendation: 'Consider assigning to longer routes' },
  ],
};

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>TransitOS Operations Dashboard</h1>
        <div className="date-time">Last updated: {new Date().toLocaleString()}</div>
      </header>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Fleet Utilization</h3>
          <p>{mockData.fleetUtilization}%</p>
          <div className="trend positive">↑ 5% vs last week</div>
        </div>
        <div className="stat-card">
          <h3>Active Trips</h3>
          <p>{mockData.activeTrips}</p>
          <div className="trend positive">↑ 12% vs yesterday</div>
        </div>
        <div className="stat-card">
          <h3>Drivers on Duty</h3>
          <p>{mockData.driversOnDuty}</p>
          <div className="trend neutral">→ Stable</div>
        </div>
        <div className="stat-card alert">
          <h3>Pending Alerts</h3>
          <p>{mockData.pendingAlerts}</p>
          <div className="trend negative">↑ 2 new</div>
        </div>
      </div>
      
      <div className="dashboard-content">
        <section className="widget">
          <h2>Fleet Activity</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Vehicle ID</th>
                  <th>Route</th>
                  <th>Driver</th>
                  <th>Status</th>
                  <th>Last Stop</th>
                </tr>
              </thead>
              <tbody>
                {mockData.fleetActivity.map(activity => (
                  <tr key={activity.id}>
                    <td>{activity.vehicleId}</td>
                    <td>{activity.route}</td>
                    <td>{activity.driver}</td>
                    <td className={activity.status === 'On Time' ? 'status-on-time' : 'status-delayed'}>
                      {activity.status}
                    </td>
                    <td>{activity.lastStop}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        
        <section className="widget">
          <h2>Maintenance Alerts</h2>
          {mockData.maintenanceAlerts.length > 0 ? (
            <div className="alerts-list">
              {mockData.maintenanceAlerts.map(alert => (
                <div key={alert.id} className={`alert-card ${alert.priority.toLowerCase()}`}>
                  <h3>Vehicle {alert.vehicleId}</h3>
                  <p><strong>Issue:</strong> {alert.issue}</p>
                  <p><strong>Priority:</strong> {alert.priority}</p>
                  <p><strong>Due Date:</strong> {alert.dueDate}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-alerts">No maintenance alerts</p>
          )}
        </section>
        
        <section className="widget">
          <h2>AI Insights & Recommendations</h2>
          {mockData.aiInsights.length > 0 ? (
            <div className="insights-list">
              {mockData.aiInsights.map(insight => (
                <div key={insight.id} className="insight-card">
                  <h3>{insight.title}</h3>
                  <p>{insight.description}</p>
                  <p className="recommendation"><strong>Recommendation:</strong> {insight.recommendation}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-insights">No insights available</p>
          )}
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
