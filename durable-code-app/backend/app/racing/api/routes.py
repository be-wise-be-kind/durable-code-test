"""Racing API route handlers.

Purpose: Provide REST API endpoints for track generation
Scope: Track retrieval and generation endpoints
Overview: This module contains the FastAPI route handlers for the racing
    game API, including simple track retrieval and procedural track generation.
Dependencies: FastAPI, Pydantic models, domain generators
Exports: FastAPI router with racing endpoints
Interfaces: REST API endpoints for track data
Implementation: Async route handlers with comprehensive validation
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.famous_tracks import (
    generate_laguna_seca_track,
    generate_monaco_style_track,
    generate_spa_inspired_track,
    generate_suzuka_style_track,
)

from ..domain.generator import generate_oval_track, generate_procedural_track
from ..geometry.boundaries import generate_boundaries_from_centerline
from ..models import Point2D, SimpleTrack, TrackBoundary, TrackGenerationParams
from ..types import (
    DEFAULT_TRACK_HEIGHT,
    DEFAULT_TRACK_PADDING,
    DEFAULT_TRACK_WIDTH,
    DIFFICULTY_PARAMS,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    MAX_TRACK_HEIGHT,
    MAX_TRACK_WIDTH,
    MIN_TRACK_HEIGHT,
    MIN_TRACK_WIDTH,
    TrackConfig,
)

# API Router
router = APIRouter(
    prefix="/api/racing",
    tags=["racing"],
    responses={
        HTTP_NOT_FOUND: {"description": "Not found"},
        HTTP_BAD_REQUEST: {"description": "Bad request"},
    },
)


def _select_track_layout(params: TrackGenerationParams, track_width: float) -> TrackBoundary:
    """Select and generate track based on layout parameter.

    Args:
        params: Track generation parameters including layout type
        track_width: Width of the track surface

    Returns:
        TrackBoundary for the selected layout

    Raises:
        ValueError: If layout generator fails
    """
    layout_generators = {
        "figure8": lambda: _generate_figure8_layout(params, track_width),
        "spa": lambda: _generate_spa_layout(params, track_width),
        "monaco": lambda: _generate_monaco_layout(params, track_width),
        "laguna": lambda: _generate_laguna_layout(params, track_width),
        "suzuka": lambda: _generate_suzuka_layout(params, track_width),
    }

    if params.layout in layout_generators:
        return layout_generators[params.layout]()

    # Build TrackConfig from params
    difficulty_config = DIFFICULTY_PARAMS[params.difficulty]
    variation = params.variation_amount if params.variation_amount is not None else difficulty_config["variation"]
    num_points = params.num_points if params.num_points is not None else difficulty_config["num_points"]

    config = TrackConfig(
        width=params.width,
        height=params.height,
        track_width=params.track_width_override if params.track_width_override is not None else track_width,
        padding=DEFAULT_TRACK_PADDING,
        num_control_points=int(num_points),
        variation_amount=float(variation),
        hairpin_chance=params.hairpin_chance if params.hairpin_chance is not None else 0.2,
        hairpin_intensity=params.hairpin_intensity if params.hairpin_intensity is not None else 2.5,
        smoothing_passes=params.smoothing_passes if params.smoothing_passes is not None else 2,
    )

    return generate_procedural_track(params.width, params.height, params.difficulty, config)


def _generate_figure8_layout(params: TrackGenerationParams, track_width: float) -> TrackBoundary:
    """Generate figure-8 track layout."""
    from ..algorithms.layouts import generate_figure8_track

    return generate_figure8_track(params.width, params.height, track_width)


def _generate_spa_layout(params: TrackGenerationParams, track_width: float) -> TrackBoundary:
    """Generate Spa-inspired track layout."""
    return generate_spa_inspired_track(
        params.width,
        params.height,
        track_width,
        generate_boundaries_from_centerline,  # type: ignore[arg-type]
    )


def _generate_monaco_layout(params: TrackGenerationParams, track_width: float) -> TrackBoundary:
    """Generate Monaco-style track layout."""
    return generate_monaco_style_track(
        params.width,
        params.height,
        track_width,
        generate_boundaries_from_centerline,  # type: ignore[arg-type]
    )


def _generate_laguna_layout(params: TrackGenerationParams, track_width: float) -> TrackBoundary:
    """Generate Laguna Seca track layout."""
    return generate_laguna_seca_track(
        params.width,
        params.height,
        track_width,
        generate_boundaries_from_centerline,  # type: ignore[arg-type]
    )


def _generate_suzuka_layout(params: TrackGenerationParams, track_width: float) -> TrackBoundary:
    """Generate Suzuka-style track layout."""
    return generate_suzuka_style_track(
        params.width,
        params.height,
        track_width,
        generate_boundaries_from_centerline,  # type: ignore[arg-type]
    )


def _find_bottom_boundary_points(
    boundaries: TrackBoundary, center_x: float, bottom_threshold: float
) -> tuple[list[Point2D], list[Point2D]]:
    """Find boundary points near the bottom of the track.

    Args:
        boundaries: Track boundary with inner and outer points
        center_x: X coordinate of track center
        bottom_threshold: Y threshold for bottom region

    Returns:
        Tuple of (inner_bottom_points, outer_bottom_points)
    """
    inner_bottom = [p for p in boundaries.inner if p.y > bottom_threshold]
    outer_bottom = [p for p in boundaries.outer if p.y > bottom_threshold]
    return inner_bottom, outer_bottom


def _calculate_start_position(boundaries: TrackBoundary, width: int, height: int) -> Point2D:
    """Calculate start position on the centerline of the track near the bottom.

    Args:
        boundaries: Track boundary with inner and outer points
        width: Canvas width
        height: Canvas height

    Returns:
        Starting position as Point2D
    """
    default = Point2D(x=width / 2, y=height - 150)

    if not boundaries.inner or not boundaries.outer:
        return default

    center_x = width / 2
    bottom_threshold = height * 0.7
    inner_bottom, outer_bottom = _find_bottom_boundary_points(boundaries, center_x, bottom_threshold)

    if not inner_bottom or not outer_bottom:
        return default

    inner_closest = min(inner_bottom, key=lambda p: abs(p.x - center_x))
    outer_closest = min(outer_bottom, key=lambda p: abs(p.x - center_x))

    return Point2D(x=(inner_closest.x + outer_closest.x) / 2, y=(inner_closest.y + outer_closest.y) / 2)


@router.get("/track/simple", response_model=SimpleTrack)
async def get_simple_track(
    width: Annotated[int, Query(ge=MIN_TRACK_WIDTH, le=MAX_TRACK_WIDTH)] = DEFAULT_TRACK_WIDTH,
    height: Annotated[int, Query(ge=MIN_TRACK_HEIGHT, le=MAX_TRACK_HEIGHT)] = DEFAULT_TRACK_HEIGHT,
) -> SimpleTrack:
    """Get a simple oval track for initial testing.

    This endpoint returns a basic oval track that can be used for testing
    physics and rendering. The track is generated procedurally based on
    the canvas dimensions.

    Args:
        width: Canvas width in pixels
        height: Canvas height in pixels

    Returns:
        SimpleTrack with boundaries and starting position

    Raises:
        HTTPException: If track generation fails
    """
    logger.info("Generating simple oval track", width=width, height=height)

    try:
        # Generate oval track boundaries
        boundaries = generate_oval_track(width, height)

        # Starting position at the bottom center of the track
        start_position = Point2D(x=width / 2, y=height - 100)

        return SimpleTrack(
            width=width, height=height, boundaries=boundaries, start_position=start_position, track_width=100
        )
    except ValueError as e:
        logger.error("Invalid track parameters", error=str(e))
        raise HTTPException(status_code=HTTP_BAD_REQUEST, detail=f"Invalid track parameters: {e}") from e
    except (KeyError, IndexError) as e:
        logger.error("Track generation failed", error=str(e))
        raise HTTPException(status_code=HTTP_BAD_REQUEST, detail="Failed to generate track") from e


@router.post("/track/generate", response_model=SimpleTrack)
async def generate_track(params: TrackGenerationParams) -> SimpleTrack:
    """Generate a procedural track based on parameters.

    Args:
        params: Track generation parameters including difficulty, seed, and layout

    Returns:
        Generated track data with specified layout

    Raises:
        HTTPException: If track generation fails

    Note:
        If a seed is provided, it creates an instance-level Random object
        to avoid manipulating global random state, which could affect other
        parts of the application.
    """
    logger.info(
        "Generating track",
        difficulty=params.difficulty,
        seed=params.seed,
        width=params.width,
        height=params.height,
        layout=params.layout,
    )

    # Note: Removed global random.seed() call to avoid manipulating application-wide
    # random state. The seed parameter is kept for API compatibility but currently
    # not used. Full implementation of seeded random generation would require
    # passing an RNG instance through the call chain (future enhancement in PR3).

    try:
        track_width = DIFFICULTY_PARAMS[params.difficulty]["track_width"]
        boundaries = _select_track_layout(params, track_width)
        start_position = _calculate_start_position(boundaries, params.width, params.height)

        return SimpleTrack(
            width=params.width,
            height=params.height,
            boundaries=boundaries,
            start_position=start_position,
            track_width=track_width,
        )
    except (ValueError, KeyError) as e:
        logger.error("Invalid generation parameters", layout=params.layout, error=str(e))
        raise HTTPException(status_code=HTTP_BAD_REQUEST, detail=f"Invalid generation parameters: {e}") from e
    except IndexError as e:
        logger.error("Track generation failed", layout=params.layout, error=str(e))
        raise HTTPException(status_code=HTTP_BAD_REQUEST, detail="Failed to generate track boundaries") from e


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for the racing API.

    Returns:
        Status indicating the API is healthy
    """
    return {"status": "healthy", "service": "racing-api"}
