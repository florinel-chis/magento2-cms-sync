import React from 'react';
import { Navigate } from 'react-router-dom';

export default function Compare() {
  // Redirect to the blocks comparison page by default
  return <Navigate to="/compare-blocks" replace />;
}