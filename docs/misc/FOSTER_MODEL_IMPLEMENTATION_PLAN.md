# David Foster Forecasting Model - BigQuery Implementation Plan

## 🎯 Overview

This document outlines the comprehensive plan to implement David Foster's sophisticated forecasting method in BigQuery, making it fully automated while preserving the statistical rigor and hockey expertise that makes his approach so effective.

## 📊 Current Status

- **David Foster's Method**: 45-60 hours of manual work per season
- **Our Goal**: <2 hours automated processing with 90%+ accuracy
- **Timeline**: 16 weeks for full implementation
- **Partnership**: Dave is a partner in this venture

## 🏗️ Architecture Overview

### BigQuery Dataset Structure
```
fantasy-snipe-ai.nhl_projections/
├── team_context                    # Team-level context data
├── toi_profiles_by_role           # Historical TOI profiles
├── player_archetypes              # Player archetype classifications
├── line_assignments               # Player line assignments
├── age_curve_adjustments          # Age curve adjustments
├── player_input_templates         # Player input templates
├── line_forecasts                 # Line-level forecasting results
├── player_forecasts               # Individual player forecasts
├── goalie_forecasts               # Goalie forecasting results
├── validation_flags               # Quality control flags
└── manual_adjustments             # Manual overrides
```

## 📋 Implementation Phases

### Phase 1: Foundation & Data Integration (Weeks 1-2)

#### 1.1 BigQuery Dataset Setup
- [x] Create `nhl_projections` dataset
- [x] Set up IAM permissions
- [x] Create table schemas
- [x] Build foundational views

#### 1.2 Data Source Integration
- [ ] Natural Stat Trick API integration
  - Individual stats (EV, PP, SH rates)
  - On-ice stats (EV, PP, SH rates)
  - Team-level CF/CA tracking
  - Goal percentage data
  - PIMs for/against tracking
- [ ] NHL API enhancement
  - Special teams ice time data
  - Line role assignments
  - Team context integration

#### 1.3 Data Cleaning & Enrichment
- [ ] Name standardization pipeline
- [ ] Birth year concatenation
- [ ] Season concatenation
- [ ] Age calculations automation
- [ ] Cross-reference data integrity checks

### Phase 2: Roster Construction & Lineup Hierarchy (Weeks 3-4)

#### 2.1 Automated Roster Construction
- [ ] Multi-source lineup building
  - PuckPedia integration (existing)
  - Daily Faceoff API integration
  - NHL API roster data
- [ ] Lineup hierarchy automation
  - 1L, 2L, 3L, 4L classification
  - 1D, 2D, 3D classification
  - PP1, PP2, PK1, PK2 assignments

#### 2.2 Historical TOI Profiles
- [ ] Create TOI profile tables
- [ ] Historical TOI data by line role
- [ ] Special teams TOI tracking
- [ ] Age-based TOI adjustments

#### 2.3 Game Played Forecasting
- [ ] Historical GP analysis
- [ ] Injury history tracking
- [ ] Young player adjustments
- [ ] Automated GP allocation

### Phase 3: Age Curves & Player Archetypes (Weeks 5-6)

#### 3.1 Age Curve Automation
- [ ] Age 26 season profiling
- [ ] CF/CA adjustments by age
- [ ] Points conversion adjustments
- [ ] Young player profiling

#### 3.2 Player Archetype Classification
- [ ] Primary archetype assignment
- [ ] Secondary archetype prediction
- [ ] Statistical pattern matching
- [ ] Machine learning enhancement

#### 3.3 Player Input Templates
- [ ] Core data extraction
- [ ] Statistical profile creation
- [ ] 3-year averages calculation

### Phase 4: Line-Level Forecasting Engine (Weeks 7-8)

#### 4.1 Individual Player Forecasting
- [ ] Line role-based forecasting
- [ ] Special teams forecasting
- [ ] TOI allocation by role
- [ ] Performance adjustment by role

#### 4.2 Line Aggregation Logic
- [ ] Forward line aggregation (sum ÷ 3)
- [ ] Defense pair aggregation (sum ÷ 2)
- [ ] Line chemistry adjustments
- [ ] TOI-weighted performance

#### 4.3 Goals Forecasting
- [ ] GF/CF ratio calculations
- [ ] GA/CA ratio calculations
- [ ] Team context factors
- [ ] Goaltending adjustments

### Phase 5: Points Allocation System (Weeks 9-10)

#### 5.1 Line-Level Points Allocation
- [ ] Formula implementation
- [ ] TOI-weighted distribution
- [ ] Performance-based weighting
- [ ] Role-based adjustments

#### 5.2 G/A Split Calculations
- [ ] Historical split analysis
- [ ] Position-based adjustments
- [ ] Age-based modifications
- [ ] Final stat breakdown

### Phase 6: Goalie Forecasting System (Weeks 9-10)

#### 6.1 GSAA Integration
- [ ] Natural Stat Trick GSAA data
- [ ] Expected vs actual performance
- [ ] Historical GSAA trends
- [ ] Team GA modifications

#### 6.2 Goalie Stat Forecasting
- [ ] GP forecasting per goalie
- [ ] Performance metrics
- [ ] SV% forecasting
- [ ] GAA calculations

### Phase 7: Validation & Quality Control (Weeks 11-12)

#### 7.1 Automated Validation Checks
- [ ] Balance verification (EV GF = GA)
- [ ] PP/SH balance verification
- [ ] CF/CA matchup validation
- [ ] Historical comparison

#### 7.2 Sniff Test Automation
- [ ] Individual player validation
- [ ] Statistical outlier detection
- [ ] Reasonability checks
- [ ] Flagging system

### Phase 8: Manual Override & Interface (Weeks 13-14)

#### 8.1 Manual Adjustment Interface
- [ ] Web-based interface
- [ ] Player search and selection
- [ ] Stat adjustment controls
- [ ] Batch editing capabilities

#### 8.2 Quality Control Workflow
- [ ] Flagged player review
- [ ] Manual review interface
- [ ] Approval workflow
- [ ] Audit trail system

### Phase 9: Automation & Scheduling (Weeks 15-16)

#### 9.1 Automated Pipeline
- [ ] Daily data updates
- [ ] Weekly forecasting runs
- [ ] Full model recalculation
- [ ] Report generation

#### 9.2 Monitoring & Alerting
- [ ] Data quality monitoring
- [ ] Processing error detection
- [ ] Performance monitoring
- [ ] Alert system

### Phase 10: Testing & Optimization (Weeks 15-16)

#### 10.1 Testing Framework
- [ ] Unit testing
- [ ] Integration testing
- [ ] Performance benchmarks
- [ ] Historical accuracy validation

#### 10.2 Optimization
- [ ] Performance tuning
- [ ] Query optimization
- [ ] Caching strategies
- [ ] Machine learning enhancement

## 🔧 Technical Implementation

### Core SQL Queries

#### Team Context Creation
```sql
WITH team_stats AS (
    SELECT 
        t.team_id,
        t.team_name,
        season,
        SUM(pgm.cf) as cf_total,
        SUM(pgm.ca) as ca_total,
        SAFE_DIVIDE(SUM(pgm.cf), SUM(pgm.cf) + SUM(pgm.ca)) * 100 as cf_pct,
        SUM(pgm.gf) as goals_for,
        SUM(pgm.ga) as goals_against,
        SAFE_DIVIDE(SUM(pgm.gf), SUM(pgm.gf) + SUM(pgm.ga)) * 100 as goal_pct
    FROM player_game_advanced_metrics_flat pgm
    JOIN games g ON pgm.game_id = g.game_id
    JOIN teams t ON pgm.team_id = t.team_id
    WHERE g.season = {season}
    GROUP BY t.team_id, t.team_name
)
```

#### Player Archetype Classification
```sql
WITH archetype_classification AS (
    SELECT 
        player_id,
        season,
        position,
        age,
        cf_pct,
        gf60,
        pts60,
        toi_avg,
        CASE 
            WHEN cf_pct >= 55.0 AND gf60 >= 25.0 AND toi_avg >= 18.0 THEN 'Elite'
            WHEN cf_pct >= 50.0 AND gf60 >= 20.0 AND toi_avg >= 15.0 THEN 'High'
            WHEN cf_pct >= 45.0 AND gf60 >= 15.0 AND toi_avg >= 12.0 THEN 'Middle'
            ELSE 'Lower'
        END as primary_archetype
    FROM player_stats
)
```

#### Line-Level Forecasting
```sql
WITH line_forecasts AS (
    SELECT 
        team_id,
        season,
        line_role,
        line_type,
        SUM(cf_forecast) as cf_forecast,
        SUM(ca_forecast) as ca_forecast,
        SUM(gf_forecast) as gf_forecast,
        SUM(ga_forecast) as ga_forecast,
        AVG(toi_forecast) as toi_forecast
    FROM individual_player_forecasts
    GROUP BY team_id, season, line_role, line_type
)
```

### Key Algorithms

#### 1. Age Curve Adjustments
```python
def calculate_age_adjustment(age, position, metric):
    """Calculate age-based adjustment factor."""
    peak_age = 26  # Peak performance age
    if age <= peak_age:
        return 1.0 + (peak_age - age) * 0.05  # 5% per year under peak
    else:
        return 1.0 - (age - peak_age) * 0.03  # 3% per year over peak
```

#### 2. Points Allocation Formula
```python
def allocate_points(line_gf, player_toi, total_line_toi, player_pts_conversion, line_gf_cf_conversion):
    """Allocate points based on Dave's formula."""
    return line_gf * (player_toi / total_line_toi) * (player_pts_conversion / line_gf_cf_conversion)
```

#### 3. Validation Checks
```python
def validate_forecasts(forecasts):
    """Run validation checks on forecasts."""
    checks = {
        'gf_ga_balance': check_gf_ga_balance(forecasts),
        'cf_ca_balance': check_cf_ca_balance(forecasts),
        'historical_comparison': check_historical_comparison(forecasts),
        'outlier_detection': detect_outliers(forecasts)
    }
    return checks
```

## 📊 Success Metrics

### Accuracy Targets
- **Match or exceed Dave's manual results**: 95%+ accuracy
- **Historical validation**: Within 5% of actual results
- **Outlier detection**: Flag 90%+ of questionable projections

### Performance Targets
- **Processing time**: <2 hours (vs 45-60 hours manual)
- **Automation level**: 90%+ automated
- **Scalability**: Handle all 32 NHL teams and 800+ players
- **Reliability**: 99.9% uptime

### Quality Targets
- **Validation coverage**: 100% of projections validated
- **Manual intervention**: <10% of projections need manual review
- **Error rate**: <1% of projections have errors
- **User satisfaction**: Dave approves of automated results

## 🚀 Getting Started

### Prerequisites
1. BigQuery project with proper permissions
2. Access to NHL API and Natural Stat Trick
3. Existing nhl_raw and nhl_processed datasets
4. Python environment with required packages

### Quick Start
```bash
# 1. Create the schema
python3 scripts/create_foster_model_schema.py

# 2. Run initial setup
python3 scripts/foster_model_core_implementation.py

# 3. Start with a single season
python3 scripts/run_foster_forecast.py --season 2024
```

### Development Workflow
1. **Local Development**: Test queries and logic locally
2. **Staging Environment**: Validate with sample data
3. **Production Deployment**: Deploy to production BigQuery
4. **Monitoring**: Track performance and accuracy
5. **Iteration**: Refine based on results

## 🔄 Maintenance & Updates

### Daily Tasks
- [ ] Data quality monitoring
- [ ] Error detection and alerting
- [ ] Performance monitoring
- [ ] User feedback collection

### Weekly Tasks
- [ ] Full forecasting run
- [ ] Validation report generation
- [ ] Manual review of flagged items
- [ ] Model performance analysis

### Monthly Tasks
- [ ] Model accuracy assessment
- [ ] Parameter tuning
- [ ] New data source integration
- [ ] Feature enhancement

## 💡 Future Enhancements

### Machine Learning Integration
- [ ] Neural networks for player development curves
- [ ] Ensemble methods for improved accuracy
- [ ] Deep learning for line chemistry
- [ ] Reinforcement learning for strategy optimization

### Advanced Analytics
- [ ] Injury prediction modeling
- [ ] Trade value optimization
- [ ] Draft pick valuation
- [ ] Contract negotiation support

### User Interface
- [ ] Web-based dashboard
- [ ] Mobile app for quick access
- [ ] API for third-party integration
- [ ] Real-time notifications

## 🏆 Conclusion

This implementation plan provides a comprehensive roadmap for automating David Foster's sophisticated forecasting method while maintaining the statistical rigor and hockey expertise that makes it so effective. The result will be a scalable, automated system that produces accurate forecasts in a fraction of the time while preserving the quality and insights of the original manual process.

The key to success is combining Dave's expertise with modern automation tools, creating a system that's both powerful and efficient. With proper implementation, this system will revolutionize fantasy hockey forecasting and provide a significant competitive advantage.
