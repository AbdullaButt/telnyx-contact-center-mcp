"""
Flask Blueprint for Analytics API endpoints
Provides HTTP access to call metrics and KPIs
"""
from flask import Blueprint, request, jsonify
from analytics_db import kpis_24h, volume_trend_days, recent_calls
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/metrics/kpis', methods=['GET'])
def get_kpis():
    """Get 24-hour KPIs for specified department or all"""
    try:
        department = request.args.get('department')
        
        # Validate department if provided
        if department and department not in {'sales', 'support', 'porting'}:
            return jsonify({"error": "Invalid department. Must be: sales, support, or porting"}), 400
        
        kpis = kpis_24h(department)
        return jsonify(kpis)
        
    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        return jsonify({"error": "Internal server error"}), 500

@analytics_bp.route('/metrics/trend', methods=['GET'])
def get_trend():
    """Get daily call volume trend"""
    try:
        days = int(request.args.get('days', 7))
        department = request.args.get('department')
        
        # Validate parameters
        if days < 1 or days > 365:
            return jsonify({"error": "Days must be between 1 and 365"}), 400
        
        if department and department not in {'sales', 'support', 'porting'}:
            return jsonify({"error": "Invalid department. Must be: sales, support, or porting"}), 400
        
        trend = volume_trend_days(days, department)
        return jsonify({
            "days": days,
            "department": department or "all",
            "trend": trend
        })
        
    except ValueError:
        return jsonify({"error": "Invalid 'days' parameter. Must be a number"}), 400
    except Exception as e:
        logger.error(f"Error getting trend: {e}")
        return jsonify({"error": "Internal server error"}), 500

@analytics_bp.route('/metrics/recent', methods=['GET'])
def get_recent_calls():
    """Get recent calls with IVR selections"""
    try:
        limit = int(request.args.get('limit', 20))
        department = request.args.get('department')
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            return jsonify({"error": "Limit must be between 1 and 1000"}), 400
        
        if department and department not in {'sales', 'support', 'porting'}:
            return jsonify({"error": "Invalid department. Must be: sales, support, or porting"}), 400
        
        calls = recent_calls(limit, department)
        return jsonify({
            "limit": limit,
            "department": department or "all",
            "calls": calls
        })
        
    except ValueError:
        return jsonify({"error": "Invalid 'limit' parameter. Must be a number"}), 400
    except Exception as e:
        logger.error(f"Error getting recent calls: {e}")
        return jsonify({"error": "Internal server error"}), 500

@analytics_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "analytics-api"})

# Error handlers
@analytics_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@analytics_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405