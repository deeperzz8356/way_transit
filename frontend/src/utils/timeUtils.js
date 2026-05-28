/**
 * Parses a time string in "HH:MM AM/PM" format and returns minutes since midnight.
 * @param {string} timeStr - Time string like "06:00 AM" or "10:30 PM"
 * @returns {number} Minutes since midnight
 */
export function parseTimeToMinutes(timeStr) {
  if (!timeStr) return 0;
  
  try {
    const cleanStr = timeStr.trim().toUpperCase();
    const parts = cleanStr.split(/\s+/);
    if (parts.length < 2) return 0;
    
    const [time, modifier] = parts;
    let [hours, minutes] = time.split(':').map(Number);
    
    if (isNaN(hours) || isNaN(minutes)) return 0;
    
    if (modifier === 'PM' && hours < 12) {
      hours += 12;
    }
    if (modifier === 'AM' && hours === 12) {
      hours = 0;
    }
    
    return hours * 60 + minutes;
  } catch (e) {
    console.error("Error parsing time string:", timeStr, e);
    return 0;
  }
}

/**
 * Calculates the difference between two time strings and returns a user-friendly duration.
 * Accounts for crossing midnight.
 * @param {string} departureTime - e.g., "10:00 PM"
 * @param {string} arrivalTime - e.g., "06:00 AM"
 * @returns {string} User-friendly duration like "8h 30m"
 */
export function calculateDuration(departureTime, arrivalTime) {
  if (!departureTime || !arrivalTime) return '';
  
  const depMins = parseTimeToMinutes(departureTime);
  let arrMins = parseTimeToMinutes(arrivalTime);
  
  if (arrMins < depMins) {
    // Trip crossed midnight
    arrMins += 24 * 60;
  }
  
  const diff = arrMins - depMins;
  const hours = Math.floor(diff / 60);
  const minutes = diff % 60;
  
  if (hours === 0) {
    return `${minutes}m`;
  }
  if (minutes === 0) {
    return `${hours}h`;
  }
  return `${hours}h ${minutes}m`;
}
